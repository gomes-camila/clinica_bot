"""
Views for handling WhatsApp webhook
"""
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

from .handlers import MessageHandler
from .twilio_helper import TwilioWhatsAppHelper

logger = logging.getLogger(__name__)

# Initialize handlers
message_handler = MessageHandler()
twilio_helper = TwilioWhatsAppHelper()


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """
    Handle incoming WhatsApp messages from Twilio
    """
    try:
        # Get message details from Twilio's POST data
        from_number = request.POST.get('From', '')
        message_body = request.POST.get('Body', '')
        
        logger.info(f"Received from {from_number}: {message_body}")
        
        # Process the message
        response = message_handler.process_message(from_number, message_body)
        
        logger.info(f"Action: {response.get('action')}")
        
        # Send appropriate response
        if response['action'] == 'send_buttons':
            # Store button mappings for this user
            button_map = {}
            for idx, btn in enumerate(response['buttons'], 1):
                button_map[str(idx)] = btn['id']
            
            message_handler.button_mappings[from_number] = button_map
            
            # Send message with buttons
            twilio_helper.send_message_with_buttons(
                from_number,
                response['body'],
                response['buttons']
            )
        
        elif response['action'] == 'send_text':
            # Send simple text message
            twilio_helper.send_text_message(from_number, response['body'])
        
        logger.info(f"Response sent to {from_number}")
        
        # Return 200 OK
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        
        # Send error message to user
        try:
            twilio_helper.send_text_message(
                from_number,
                'Desculpe, algo deu errado. Digite "menu" para tentar novamente.'
            )
        except:
            pass
        
        return HttpResponse(status=500)