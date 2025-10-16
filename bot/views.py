"""
Views for handling WhatsApp webhook with interactive buttons
"""
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

from .handlers import MessageHandler
from .twilio_helper import TwilioWhatsAppHelper

logger = logging.getLogger(__name__)

# Initialize Twilio helper
twilio_helper = TwilioWhatsAppHelper()

# Store button mappings per conversation
button_mappings = {}


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
        button_response = request.POST.get('ButtonPayload', '')
        
        logger.info(f"Received from {from_number}: {message_body}")
        if button_response:
            logger.info(f"Button clicked: {button_response}")
        
        # Determine button ID
        button_id = None
        
        # Check if it's an actual button response from WhatsApp
        if button_response:
            button_id = button_response
        # Check if user typed a number (fallback for non-button mode)
        elif message_body.strip().isdigit():
            last_buttons = button_mappings.get(from_number, {})
            button_id = last_buttons.get(message_body.strip())
        
        # Process the message and get response
        response_data = MessageHandler.process_message(
            from_number, 
            message_body,
            button_id=button_id
        )
        
        # Send appropriate response
        if response_data['type'] == 'buttons':
            buttons = response_data.get('buttons', [])
            
            # Store button mapping for this user (for number fallback)
            button_mappings[from_number] = {
                str(idx): btn['id'] 
                for idx, btn in enumerate(buttons, 1)
            }
            
            # Try to send with interactive buttons
            try:
                twilio_helper.send_button_message(
                    from_number,
                    response_data['body'],
                    buttons
                )
            except Exception as e:
                logger.warning(f"Couldn't send buttons, using text fallback: {str(e)}")
                # Fallback to numbered text
                twilio_helper.send_text_with_options(
                    from_number,
                    response_data['body'],
                    buttons
                )
        else:
            # Send simple text message
            twilio_helper.send_text_message(
                from_number,
                response_data['body']
            )
        
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