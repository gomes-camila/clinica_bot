"""
Twilio helper for sending WhatsApp messages with dynamic content
"""
from twilio.rest import Client
from decouple import config
import json
import logging

logger = logging.getLogger(__name__)


class TwilioWhatsAppHelper:
    """Helper class for sending WhatsApp messages via Twilio"""
    
    def __init__(self):
        self.client = Client(
            config('TWILIO_ACCOUNT_SID'),
            config('TWILIO_AUTH_TOKEN')
        )
        self.from_number = config('TWILIO_WHATSAPP_NUMBER')
    
    def send_message_with_buttons(self, to_number, body_text, buttons):
        """
        Send WhatsApp message with buttons (numbered fallback)
        
        Args:
            to_number: Recipient WhatsApp number
            body_text: Message body text
            buttons: List of dicts with 'id' and 'title' keys
            
        Returns:
            Message SID
        """
        try:
            # Format message with numbered buttons
            formatted_text = f"{body_text}\n\n"
            for idx, btn in enumerate(buttons, 1):
                formatted_text += f"{idx}. {btn['title']}\n"
            formatted_text += "\nResponda com o número da opção."
            
            message = self.client.messages.create(
                from_=self.from_number,
                to=to_number,
                body=formatted_text
            )
            
            logger.info(f"Message sent: {message.sid}")
            return message.sid
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise
    
    def send_text_message(self, to_number, body_text):
        """
        Send simple text message
        
        Args:
            to_number: Recipient WhatsApp number
            body_text: Message body text
            
        Returns:
            Message SID
        """
        try:
            message = self.client.messages.create(
                from_=self.from_number,
                to=to_number,
                body=body_text
            )
            
            logger.info(f"Text message sent: {message.sid}")
            return message.sid
            
        except Exception as e:
            logger.error(f"Error sending text message: {str(e)}")
            raise