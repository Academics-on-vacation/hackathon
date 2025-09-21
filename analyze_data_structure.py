import pandas as pd
import os

def analyze_excel_structure(file_path):
    """Анализирует структуру Excel файла - читает первые строки всех листов"""
    print(f"\n=== Анализ файла: {file_path} ===")
    
    try:
        # Получаем список всех листов
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"Найдено листов: {len(sheet_names)}")
        print(f"Названия листов: {sheet_names}")
        
        for sheet_name in sheet_names:
            print(f"\n--- Лист: {sheet_name} ---")
            try:
                # Читаем первые 5 строк листа
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=5)
                print(f"Размер листа (первые 5 строк): {df.shape}")
                print(f"Колонки: {list(df.columns)}")
                print("Первые строки данных:")
                print(df.to_string())
                
                # Проверяем типы данных
                print(f"\nТипы данных:")
                for col in df.columns:
                    print(f"  {col}: {df[col].dtype}")
                    
            except Exception as e:
                print(f"Ошибка при чтении листа {sheet_name}: {e}")
                
    except Exception as e:
        print(f"Ошибка при открытии файла: {e}")

def main():
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        print(f"Папка {data_dir} не найдена")
        return
    
    # Анализируем все Excel файлы в папке data
    for filename in os.listdir(data_dir):
        if filename.endswith('.xlsx'):
            file_path = os.path.join(data_dir, filename)
            analyze_excel_structure(file_path)

if __name__ == "__main__":
    main()