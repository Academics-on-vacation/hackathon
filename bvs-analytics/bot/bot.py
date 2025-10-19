
import sys
import os
import logging
import tempfile
from pathlib import Path
from typing import Optional

# Добавляем путь к backend для импорта модулей
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sqlalchemy.orm import Session
from app.services.flight_service import FlightService
from app.services.flights_analytics_service import FlightsAnalyticsService
from app.services.latex_generator import generate_report
from app.core.database import get_db

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FlightReportBot:
    """Telegram бот для генерации отчетов по полетам БПЛА из Excel файлов"""
    
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(
            MessageHandler(
                filters.Document.FileExtension("xlsx"), 
                self.handle_excel_file
            )
        )
        self.application.add_handler(
            MessageHandler(
                filters.Document.ALL & ~filters.Document.FileExtension("xlsx"),
                self.handle_wrong_format
            )
        )
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        welcome_text = (
            "🛩️ *Добро пожаловать в Flight Report Bot\\!*\\n\\n"
            "Я помогу вам сгенерировать отчет по полетам БПЛА из Excel файлов\\.\\n\\n"
            "📋 *Как пользоваться:*\\n"
            "1\\. Отправьте мне Excel файл \\(только \\.xlsx\\)\\n"
            "2\\. Дождитесь обработки данных\\n" 
            "3\\. Получите PDF отчет\\n\\n"
            "Используйте /help для получения дополнительной информации\\."
        )
        await update.message.reply_text(
            welcome_text, 
            parse_mode='MarkdownV2'
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        help_text = (
            "🔧 *Справка по использованию*\\n\\n"
            "*Поддерживаемые форматы:*\\n"
            "• Excel файлы \\(\\.xlsx\\)\\n"
            "• Файлы с листами по регионам\\n"
            "• Агрегированные данные\\n\\n"
            "*Что включает отчет:*\\n"
            "• Общая статистика полетов\\n"
            "• Распределение по регионам\\n"
            "• Анализ по времени\\n"
            "• Типы БПЛА и операторы\\n"
            "• Графики и диаграммы\\n\\n"
            "*Команды:*\\n"
            "/start \\- начать работу\\n"
            "/help \\- эта справка"
        )
        await update.message.reply_text(
            help_text,
            parse_mode='MarkdownV2'
        )
    
    async def handle_wrong_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик файлов неправильного формата"""
        await update.message.reply_text(
            "❌ Поддерживаются только Excel файлы (.xlsx)\\n"
            "Пожалуйста, отправьте файл в правильном формате\\.",
            parse_mode='MarkdownV2'
        )
    
    async def handle_excel_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Основной обработчик Excel файлов"""
        user = update.message.from_user
        document = update.message.document
        
        logger.info(f"User {user.id} ({user.username}) uploaded file: {document.file_name}")
        
        # Проверяем размер файла
        if document.file_size > 50 * 1024 * 1024:  # 50MB
            await update.message.reply_text(
                "❌ Файл слишком большой\\. Максимальный размер: 50MB",
                parse_mode='MarkdownV2'
            )
            return
        
        # Сообщаем о начале обработки
        processing_message = await update.message.reply_text(
            "📊 Обрабатываю файл\\.\\.\\. Это может занять несколько минут\\.",
            parse_mode='MarkdownV2'
        )
        
        temp_file_path = None
        try:
            # Скачиваем файл
            temp_file_path = await self._download_file(document, context)
            
            # Обновляем статус
            await processing_message.edit_text(
                "📈 Импортирую данные в базу\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # Импортируем данные
            import_result = await self._import_data(temp_file_path)
            
            if import_result['imported'] == 0:
                await self._handle_import_error(update, import_result)
                return
            
            # Обновляем статус
            await processing_message.edit_text(
                f"✅ Импортировано {import_result['imported']} записей\\n"
                f"📑 Генерирую отчет\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # Генерируем отчет
            report_path = await self._generate_report()
            
            if not report_path or not Path(report_path).exists():
                await processing_message.edit_text(
                    "❌ Ошибка при генерации отчета\\.",
                    parse_mode='MarkdownV2'
                )
                return
            
            # Отправляем отчет
            await self._send_report(update, report_path, import_result)
            
            # Удаляем сообщение о процессе
            await processing_message.delete()
            
        except Exception as e:
            logger.error(f"Error processing file from user {user.id}: {str(e)}")
            await processing_message.edit_text(
                f"❌ Произошла ошибка при обработке файла:\\n`{str(e)}`",
                parse_mode='MarkdownV2'
            )
        finally:
            # Очищаем временные файлы
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")
    
    async def _download_file(self, document: Document, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Скачивает файл во временную директорию"""
        file = await context.bot.get_file(document.file_id)
        
        # Создаем временный файл с правильным расширением
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.xlsx',
            prefix=f'telegram_bot_{document.file_unique_id}_'
        )
        temp_file.close()
        
        # Скачиваем файл
        await file.download_to_drive(temp_file.name)
        
        return temp_file.name
    
    async def _import_data(self, file_path: str) -> dict:
        """Импортирует данные из Excel файла"""
        # Эмулируем UploadFile объект для совместимости с FlightService
        class MockUploadFile:
            def __init__(self, file_path: str):
                self.file_path = file_path
                self.filename = Path(file_path).name
            
            async def read(self) -> bytes:
                with open(self.file_path, 'rb') as f:
                    return f.read()
        
        # Получаем сессию БД
        db = next(get_db())
        
        try:
            # Создаем сервис и импортируем данные
            flight_service = FlightService(db)
            mock_file = MockUploadFile(file_path)
            
            result = await flight_service.import_from_excel(mock_file)
            return result
            
        finally:
            db.close()
    
    async def _generate_report(self) -> Optional[str]:
        """Генерирует отчет"""
        # Получаем сессию БД
        db = next(get_db())
        
        try:
            # Генерируем отчет для всех данных
            report_path = generate_report(
                db=db,
                begin_date=None,
                end_date=None, 
                region=None,
                extended=False
            )
            return report_path
            
        finally:
            db.close()
    
    async def _send_report(self, update: Update, report_path: str, import_result: dict) -> None:
        """Отправляет готовый отчет пользователю"""
        # Формируем статистику импорта
        stats_text = (
            f"📊 *Отчет готов\\!*\\n\\n"
            f"✅ Обработано записей: {import_result['imported']}\\n"
        )
        
        if import_result.get('errors'):
            error_count = len(import_result['errors'])
            stats_text += f"⚠️ Предупреждений: {error_count}\\n"
        
        # Отправляем статистику
        await update.message.reply_text(stats_text, parse_mode='MarkdownV2')
        
        # Отправляем PDF файл
        with open(report_path, 'rb') as report_file:
            await update.message.reply_document(
                document=report_file,
                filename=Path(report_path).name,
                caption="📋 Отчет по полетам БПЛА"
            )
    
    async def _handle_import_error(self, update: Update, import_result: dict) -> None:
        """Обрабатывает ошибки импорта"""
        error_text = "❌ *Не удалось импортировать данные*\\n\\n"
        
        errors = import_result.get('errors', [])
        if errors:
            error_text += "*Ошибки:*\\n"
            # Показываем только первые 3 ошибки для краткости
            for error in errors[:3]:
                escaped_error = error.replace('.', '\\.').replace('-', '\\-').replace('(', '\\(').replace(')', '\\)')
                error_text += f"• {escaped_error}\\n"
            
            if len(errors) > 3:
                error_text += f"• \\.\\.\\. и еще {len(errors) - 3} ошибок\\n"
        
        error_text += "\\nПроверьте формат файла и попробуйте еще раз\\."
        
        await update.message.reply_text(error_text, parse_mode='MarkdownV2')
    
    def run(self) -> None:
        """Запускает бота"""
        logger.info("Starting Flight Report Bot...")
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    
    async def stop(self) -> None:
        """Останавливает бота"""
        logger.info("Stopping Flight Report Bot...")
        await self.application.stop()


def main():
    """Точка входа"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Создаем и запускаем бота
    bot = FlightReportBot(token)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")


if __name__ == '__main__':
    main()
