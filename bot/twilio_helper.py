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
    
    def send_template_message(self, to_number, template_name, language='pt_BR', components=None):
        """
        Send WhatsApp message using Twilio's Template
        
        Args:
            to_number: Recipient WhatsApp number
            template_name: The name/SID of the template to use
            language: Template language code (default: pt_BR)
            components: List of template components (optional)
            
        Returns:
            Message SID
        """
        try:
            message = self.client.messages.create(
                from_=self.from_number,
                to=to_number,
                content_sid=template_name,
                content_variables=json.dumps(components) if components else None
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