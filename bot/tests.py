from twilio.rest import Client
from calendar_service import CalendarService
from decouple import config

# Configurações do Twilio
TWILIO_SID = config('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = config('TWILIO_WHATSAPP_NUMBER')

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Número de teste
patient_number = "whatsapp:+554184180726"  # inclua o prefixo 'whatsapp:'

# Inicializa o CalendarService
calendar = CalendarService()
available_dates = calendar.get_available_dates()

# Formata mensagem
message_text = "Olá! Horários disponíveis nos próximos dias:\n"
for date in available_dates:
    message_text += f"- {calendar.format_date(date)}\n"

# Envia mensagem via Twilio
message = client.messages.create(
    from_=TWILIO_WHATSAPP_NUMBER,
    to=patient_number,
    body=message_text
)

print(f"Mensagem enviada! SID: {message.sid}")