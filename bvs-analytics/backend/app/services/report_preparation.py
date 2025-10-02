# visualize_full.py
#
# Скрипт строит набор графиков на основе данных API и сохраняет их в папку ./plots.
# Адреса API приведены к виду: http://127.0.0.1:8000/api/v1/...
# При каждом запуске папка ./plots очищается.
# Диаграмма ByType оставлена круговой (donut), но настроена так, чтобы не было наложений:
#  - подписи категорий вынесены в легенду
#  - на самой диаграмме показываются проценты только для сегментов >= MIN_PCT
#  - мелкие категории агрегируются в "Другие"
#  - угол и расстояния подобраны для аккуратного вида

import os
import shutil
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from .flights_analytics_service import *

# -----------------------------
# Конфигурация
# -----------------------------
SAVE_DIR = "plots"


def prepare_data():
    # -----------------------------
    # Стиль графиков
    # -----------------------------
    plt.style.use("seaborn-v0_8-whitegrid")
    sns.set_context("talk", font_scale=1.05)
    plt.rcParams.update({
        "figure.autolayout": True,
        "axes.titlesize": 18,
        "axes.labelsize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "savefig.dpi": 150,
    })

    # -----------------------------
    # Очистка папки ./plots
    # -----------------------------
    if os.path.exists(SAVE_DIR):
        shutil.rmtree(SAVE_DIR)
    os.makedirs(SAVE_DIR, exist_ok=True)
    print("[INFO] Папка plots очищена")

    # -----------------------------
    # Загрузка данных
    # -----------------------------

    resp = FlightsAnalyticsService.get_general_statistics()
    stats = resp.json()



    # Ожидаемая структура stats:
    # {
    #   "duration": int,
    #   "avg_duration": float,
    #   "flights": int,
    #   "month": {...},
    #   "weekdays": {...},
    #   "times": {...},
    #   "types": {...},
    #   "operators": {...},
    #   "regions": { "<id>": {"name": str, "flights": int, "avgDuration": float, "duration": int}, ... },
    #   "top": [...]
    # }

    # -----------------------------
    # Основные метрики
    # -----------------------------
    total_flights = stats.get("flights", 0)
    total_duration = stats.get("duration", 0)
    avg_duration = stats.get("avg_duration", 0)
    unique_uav_types = len(stats.get("types", {}) or {})
    flight_centers = len(stats.get("operators", {}) or {})

    metrics = {
        "totalFlights": total_flights,
        "totalDuration": total_duration,
        "avgDuration": avg_duration,
        "uniqueUAVTypes": unique_uav_types,
        "flightCenters": flight_centers
    }

    with open(os.path.join(SAVE_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    # Карточка с метриками (png)
    fig, axs = plt.subplots(1, 5, figsize=(20, 4))
    fig.suptitle("Основные метрики", fontsize=20, fontweight="bold")

    cards = [
        ("Всего полётов", f"{total_flights:,}".replace(",", " ")),
        ("Общая длительность", f"{total_duration:,} мин".replace(",", " ")),
        ("Средняя длительность", f"{avg_duration:.1f} мин"),
        ("Типы БПЛА", f"{unique_uav_types}"),
        ("Операторов", f"{flight_centers}")
    ]

    for ax, (title, value) in zip(axs, cards):
        ax.axis("off")
        ax.text(0.5, 0.65, title, fontsize=14, ha="center", color="gray")
        ax.text(0.5, 0.35, value, fontsize=24, ha="center", fontweight="bold")

    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_DIR, "metrics.png"))
    plt.close()
    print("[INFO] Сохранены метрики: metrics.json, metrics.png")

    # -----------------------------
    # Вспомогательные преобразования
    # -----------------------------
    regions_map = stats.get("regions", {}) or {}
    # Преобразуем словарь регионов в DataFrame
    if regions_map:
        df_regions = (
            pd.DataFrame(regions_map)
            .T  # ключи — это id регионов, переносим их в строки
            .reset_index(drop=True)
        )
    else:
        df_regions = pd.DataFrame(columns=["name", "flights", "duration", "avgDuration"])

    # -----------------------------
    # График: Топ-15 регионов по количеству полётов
    # -----------------------------
    if not df_regions.empty:
        df_top_count = df_regions.sort_values("flights", ascending=False).head(15)
        plt.figure(figsize=(12, 7))
        sns.barplot(data=df_top_count, x="flights", y="name", color="#3b82f6")
        plt.title("Топ-15 регионов по количеству полётов")
        plt.xlabel("Количество полётов")
        plt.ylabel("Регион")
        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_DIR, "topByCount.png"))
        plt.close()
        print("[INFO] Сохранён график: topByCount.png")

    # -----------------------------
    # График: Топ-15 регионов по суммарной длительности
    # -----------------------------
    if not df_regions.empty:
        df_top_duration = df_regions.sort_values("duration", ascending=False).head(15)
        plt.figure(figsize=(12, 7))
        sns.barplot(data=df_top_duration, x="duration", y="name", color="#10b981")
        plt.title("Топ-15 регионов по суммарной длительности полётов")
        plt.xlabel("Длительность (мин.)")
        plt.ylabel("Регион")
        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_DIR, "topByDuration.png"))
        plt.close()
        print("[INFO] Сохранён график: topByDuration.png")

    # -----------------------------
    # График: Распределение полётов по времени суток
    # -----------------------------
    times = stats.get("times", {}) or {}
    if times:
        plt.figure(figsize=(12, 6))
        plt.plot(list(times.keys()), list(times.values()), marker="o", linewidth=2)
        plt.title("Распределение полётов по времени суток")
        plt.xlabel("Час")
        plt.ylabel("Количество полётов")
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_DIR, "byHour.png"))
        plt.close()
        print("[INFO] Сохранён график: byHour.png")

    # -----------------------------
    # График: Полёты по дням недели
    # -----------------------------
    weekdays = stats.get("weekdays", {}) or {}
    if weekdays:
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(weekdays.keys()), y=list(weekdays.values()), color="#3b82f6")
        plt.title("Полёты по дням недели")
        plt.xlabel("День недели")
        plt.ylabel("Количество полётов")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_DIR, "byWeekday.png"))
        plt.close()
        print("[INFO] Сохранён график: byWeekday.png")

    # -----------------------------
    # График: Полёты по месяцам
    # -----------------------------
    months = stats.get("month", {}) or {}
    if months:
        plt.figure(figsize=(12, 6))
        sns.barplot(x=list(months.keys()), y=list(months.values()), color="#10b981")
        plt.title("Полёты по месяцам")
        plt.xlabel("Месяц")
        plt.ylabel("Количество полётов")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_DIR, "byMonth.png"))
        plt.close()
        print("[INFO] Сохранён график: byMonth.png")

    # -----------------------------
    # График: Распределение по типам БПЛА (КРУГОВАЯ ДИАГРАММА, БЕЗ НАЛОЖЕНИЙ)
    # -----------------------------
    # Подход:
    #  - категории с малой долей объединяются в "Другие"
    #  - подписи категорий не рисуем на сегментах, только проценты (только для крупных сегментов)
    #  - легенду с названиями и значениями выводим справа
    types = stats.get("types", {}) or {}
    if types:
        labels = list(types.keys())
        sizes = list(types.values())
        total = sum(sizes) if sizes else 0

        # Если категорий много, берём топ-N и агрегируем остальные
        TOP_N = 10
        if len(labels) > TOP_N:
            pairs = sorted(zip(labels, sizes), key=lambda x: x[1], reverse=True)
            top_labels, top_sizes = zip(*pairs[:TOP_N])
            other_size = total - sum(top_sizes)
            labels = list(top_labels) + (["Другие"] if other_size > 0 else [])
            sizes = list(top_sizes) + ([other_size] if other_size > 0 else [])

        # Порог для показа процентов на сегменте (иначе пустая строка -> нет текста -> нет наложения)
        MIN_PCT = 4.0  # показываем проценты только если сегмент >= 4%

        def autopct_fmt(pct):
            return f"{pct:.1f}%" if pct >= MIN_PCT else ""

        # Подготовка подписей для легенды: "Тип — число (доля%)"
        legend_labels = []
        for lab, sz in zip(labels, sizes):
            share = (sz / total * 100) if total else 0
            legend_labels.append(f"{lab} — {sz:,} ({share:.1f}%)".replace(",", " "))

        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(
            sizes,
            autopct=autopct_fmt,
            startangle=140,
            pctdistance=0.7,                 # проценты ближе к центру
            textprops={"fontsize": 11, "color": "white"},
            wedgeprops={"width": 0.5}        # делаем donut: так проценты лучше читаются
        )

        # Сами подписи категорий на сегментах не показываем — они в легенде
        for t in texts:
            t.set_visible(False)

        ax.axis("equal")
        plt.title("Распределение полётов по типам БПЛА", fontsize=16, fontweight="bold")

        # Легенда справа, вне области рисунка
        ax.legend(
            wedges,
            legend_labels,
            title="Типы БПЛА",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            fontsize=11,
            title_fontsize=13,
            borderaxespad=0.0
        )

        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_DIR, "byType.png"), bbox_inches="tight")
        plt.close()
        print("[INFO] Сохранён график: byType.png")

    print("\nГотово. Все графики и метрики сохранены в папке:", SAVE_DIR)
