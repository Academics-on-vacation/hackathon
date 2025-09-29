from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from hackathon.FastApifunctional.database import get_db
import uvicorn

app = FastAPI(title="Flights API — Stats")

RU_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
    7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}
RU_WEEKDAYS = {
    0: "Воскресенье", 1: "Понедельник", 2: "Вторник", 3: "Среда",
    4: "Четверг", 5: "Пятница", 6: "Суббота"
}

@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # 1) Общая статистика: количество рейсов, суммарная и средняя длительность (в секундах)
    q1 = text("""
        SELECT
            COUNT(*) AS flights,
            COALESCE(SUM(duration_minutes),0) AS sum_min,
            AVG(duration_minutes) AS avg_min
        FROM flights
    """)
    r1 = await db.execute(q1)
    row1 = r1.first()
    flights = int(row1.flights or 0)
    sum_min = float(row1.sum_min or 0)
    avg_min = float(row1.avg_min or 0) if row1.avg_min is not None else 0.0

    duration_seconds = int(sum_min * 60)
    avg_duration_seconds = (avg_min * 60) if avg_min else 0.0

    # 2) По месяцам (departure_time)
    q_month = text("""
        SELECT EXTRACT(MONTH FROM departure_time)::int AS m, COUNT(*) AS cnt
        FROM flights
        WHERE departure_time IS NOT NULL
        GROUP BY m
    """)
    r_month = await db.execute(q_month)
    month = {}
    for m, cnt in r_month.fetchall():
        month[RU_MONTHS.get(int(m), str(int(m)))] = int(cnt)

    # 3) По дням недели
    q_wd = text("""
        SELECT EXTRACT(DOW FROM departure_time)::int AS d, COUNT(*) AS cnt
        FROM flights
        WHERE departure_time IS NOT NULL
        GROUP BY d
    """)
    r_wd = await db.execute(q_wd)
    weekdays = {}
    for d, cnt in r_wd.fetchall():
        weekdays[RU_WEEKDAYS.get(int(d), str(int(d)))] = int(cnt)

    # 4) По типам ВС
    q_types = text("""
        SELECT COALESCE(aircraft_type, '') AS tp, COUNT(*) AS cnt
        FROM flights
        GROUP BY tp
        ORDER BY cnt DESC
    """)
    r_types = await db.execute(q_types)
    types = {tp: int(cnt) for tp, cnt in r_types.fetchall()}

    # 5) По операторам
    q_ops = text("""
        SELECT COALESCE(operator, '') AS op, COUNT(*) AS cnt
        FROM flights
        GROUP BY op
        ORDER BY cnt DESC
        LIMIT 1000
    """)
    r_ops = await db.execute(q_ops)
    operators = {op: int(cnt) for op, cnt in r_ops.fetchall()}

    # 6) По часу вылета (H:00)
    q_times = text("""
        SELECT EXTRACT(HOUR FROM departure_time)::int AS h, COUNT(*) AS cnt
        FROM flights
        WHERE departure_time IS NOT NULL
        GROUP BY h
        ORDER BY h
    """)
    r_times = await db.execute(q_times)
    times = {}
    for h, cnt in r_times.fetchall():
        times[f"{h}:00"] = int(cnt)

    # 7) Регионы (join regions)
    q_regions = text("""
        SELECT f.region_id, r.name, COUNT(*) AS cnt, COALESCE(SUM(f.duration_minutes),0) AS sum_min
        FROM flights f
        LEFT JOIN regions r ON r.id = f.region_id
        GROUP BY f.region_id, r.name
        ORDER BY cnt DESC
        LIMIT 1000
    """)
    r_regions = await db.execute(q_regions)
    regions = {}
    for region_id, name, cnt, sum_min_region in r_regions.fetchall():
        key = str(region_id) if region_id is not None else "-10"
        regions[key] = {
            "name": name or "Не определено",
            "flights": int(cnt),
            "avgDuration": int((sum_min_region / cnt) * 60) if cnt and sum_min_region else 0,
            "duration": int(sum_min_region * 60)
        }

    result = {
        "duration": duration_seconds,
        "avg_duration": avg_duration_seconds,
        "flights": flights,
        "month": month,
        "weekdays": weekdays,
        "types": types,
        "operators": operators,
        "times": times,
        "regions": regions,
    }

    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
