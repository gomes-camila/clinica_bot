from calendar_service import CalendarService

calendar = CalendarService()

# Pega próximos 7 dias disponíveis
available_dates = calendar.get_available_dates(days_ahead=7)

for date in available_dates:
    slots = calendar.get_available_slots(date)
    print(f"Data: {calendar.format_date(date)}")
    for slot in slots:
        print(f" - Horário disponível: {calendar.format_time(slot)}")