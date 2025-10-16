"""
Message handlers for WhatsApp receptionist bot with Google Calendar integration
"""
from .calendar_service import CalendarService
import logging

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles incoming WhatsApp messages and generates responses"""
    
    # In-memory storage for conversation state and button mappings
    conversations = {}
    button_mappings = {}
    
    def __init__(self):
        self.calendar = CalendarService()
    
    def process_message(self, from_number, message_body):
        """
        Process incoming message and return appropriate response
        
        Args:
            from_number: WhatsApp number of sender
            message_body: Text content of the message
            
        Returns:
            dict: Response with 'action', 'body', and optional 'buttons'
        """
        message = message_body.strip().lower()
        
        # Get or initialize conversation state
        state = self.conversations.get(from_number, {'step': 'menu'})
        
        # Handle menu navigation
        if message in ['menu', 'start', 'hello', 'hi', 'olá', 'oi']:
            self.conversations[from_number] = {'step': 'menu'}
            return self._show_main_menu()
        
        # Get button mapping for this user's last message
        button_map = self.button_mappings.get(from_number, {})
        button_id = button_map.get(message)
        
        # Handle main menu
        if state['step'] == 'menu':
            return self._handle_main_menu(from_number, message, button_id)
        
        # Handle patient name input
        elif state['step'] == 'get_patient_name':
            return self._handle_patient_name(from_number, message_body)
        
        # Handle date selection
        elif state['step'] == 'select_date':
            return self._handle_date_selection(from_number, message, button_id)
        
        # Handle time selection
        elif state['step'] == 'select_time':
            return self._handle_time_selection(from_number, message, button_id)
        
        # Handle confirmation
        elif state['step'] == 'confirm':
            return self._handle_confirmation(from_number, message, button_id)
        
        # Default fallback
        return {
            'action': 'send_text',
            'body': "Desculpe, não entendi. Digite 'menu' para voltar ao menu principal."
        }
    
    def _show_main_menu(self):
        """Show main menu with appointment types"""
        buttons = [
            {'id': 'appointment_1', 'title': 'Consulta Geral'},
            {'id': 'appointment_2', 'title': 'Consulta Especializada'},
            {'id': 'office_hours', 'title': 'Horário de Atendimento'}
        ]
        
        return {
            'action': 'send_buttons',
            'body': 'Olá! Bem-vindo à Clínica Dr. Silva 🏥\n\nQual serviço deseja agendar?',
            'buttons': buttons
        }
    
    def _handle_main_menu(self, from_number, message, button_id):
        """Handle main menu selection"""
        if button_id in ['appointment_1', 'appointment_2']:
            # Store appointment type and ask for patient name
            appointment_names = {
                'appointment_1': 'Consulta Geral',
                'appointment_2': 'Consulta Especializada'
            }
            
            self.conversations[from_number] = {
                'step': 'get_patient_name',
                'appointment_type': button_id,
                'appointment_name': appointment_names[button_id]
            }
            
            return {
                'action': 'send_text',
                'body': 'Perfeito! Para continuar, preciso de algumas informações.\n\nQual é o seu nome completo?'
            }
        
        elif button_id == 'office_hours':
            return {
                'action': 'send_text',
                'body': """📅 Horário de Atendimento:

Segunda a Sexta: 09:00 - 17:00
Sábado: Fechado
Domingo: Fechado

⏰ Duração da consulta: 30 minutos

Digite 'menu' para voltar ao menu principal."""
            }
        
        return {
            'action': 'send_text',
            'body': "Por favor, escolha uma opção válida ou digite 'menu'."
        }
    
    def _handle_patient_name(self, from_number, name):
        """Handle patient name input and show available dates"""
        state = self.conversations[from_number]
        state['patient_name'] = name
        state['step'] = 'select_date'
        self.conversations[from_number] = state
        
        # Get available dates from calendar
        try:
            available_dates = self.calendar.get_available_dates(days_ahead=14)
            
            if not available_dates:
                return {
                    'action': 'send_text',
                    'body': 'Desculpe, não há datas disponíveis no momento. Entre em contato pelo telefone (41) 3333-4444.\n\nDigite "menu" para voltar.'
                }
            
            # Create buttons for available dates
            buttons = []
            date_map = {}
            for idx, date in enumerate(available_dates, 1):
                formatted_date = self.calendar.format_date(date)
                buttons.append({
                    'id': f'date_{idx}',
                    'title': formatted_date
                })
                date_map[str(idx)] = date
            
            # Store date mapping
            state['available_dates'] = date_map
            self.conversations[from_number] = state
            
            return {
                'action': 'send_buttons',
                'body': f'Obrigado, {name}!\n\nEscolha uma data disponível:',
                'buttons': buttons
            }
            
        except Exception as e:
            logger.error(f"Error getting available dates: {str(e)}")
            return {
                'action': 'send_text',
                'body': 'Desculpe, houve um erro ao buscar as datas disponíveis. Tente novamente mais tarde.\n\nDigite "menu" para voltar.'
            }
    
    def _handle_date_selection(self, from_number, message, button_id):
        """Handle date selection and show available times"""
        state = self.conversations[from_number]
        
        # Extract date index from button_id or message
        date_idx = None
        if button_id and button_id.startswith('date_'):
            date_idx = button_id.split('_')[1]
        elif message.isdigit():
            date_idx = message
        
        if not date_idx or date_idx not in state.get('available_dates', {}):
            return {
                'action': 'send_text',
                'body': 'Por favor, escolha uma data válida ou digite "menu" para voltar.'
            }
        
        selected_date = state['available_dates'][date_idx]
        state['selected_date'] = selected_date
        state['step'] = 'select_time'
        self.conversations[from_number] = state
        
        # Get available time slots
        try:
            available_slots = self.calendar.get_available_slots(selected_date)
            
            if not available_slots:
                return {
                    'action': 'send_text',
                    'body': 'Desculpe, não há horários disponíveis nesta data. Digite "menu" para escolher outra data.'
                }
            
            # Create buttons for available times
            buttons = []
            time_map = {}
            for idx, slot in enumerate(available_slots, 1):
                formatted_time = self.calendar.format_time(slot)
                buttons.append({
                    'id': f'time_{idx}',
                    'title': formatted_time
                })
                time_map[str(idx)] = slot
            
            # Store time mapping
            state['available_times'] = time_map
            self.conversations[from_number] = state
            
            formatted_date = self.calendar.format_date(selected_date)
            
            return {
                'action': 'send_buttons',
                'body': f'Data selecionada: {formatted_date}\n\nEscolha um horário:',
                'buttons': buttons
            }
            
        except Exception as e:
            logger.error(f"Error getting available times: {str(e)}")
            return {
                'action': 'send_text',
                'body': 'Desculpe, houve um erro ao buscar os horários. Tente novamente.\n\nDigite "menu" para voltar.'
            }
    
    def _handle_time_selection(self, from_number, message, button_id):
        """Handle time selection and show confirmation"""
        state = self.conversations[from_number]
        
        # Extract time index
        time_idx = None
        if button_id and button_id.startswith('time_'):
            time_idx = button_id.split('_')[1]
        elif message.isdigit():
            time_idx = message
        
        if not time_idx or time_idx not in state.get('available_times', {}):
            return {
                'action': 'send_text',
                'body': 'Por favor, escolha um horário válido ou digite "menu" para voltar.'
            }
        
        selected_time = state['available_times'][time_idx]
        state['selected_time'] = selected_time
        state['step'] = 'confirm'
        self.conversations[from_number] = state
        
        # Show confirmation
        formatted_date = self.calendar.format_date(state['selected_date'])
        formatted_time = self.calendar.format_time(selected_time)
        
        confirmation_text = f"""📋 Resumo do Agendamento:

👤 Paciente: {state['patient_name']}
🏥 Serviço: {state['appointment_name']}
📅 Data: {formatted_date}
⏰ Horário: {formatted_time}

Deseja confirmar este agendamento?"""
        
        buttons = [
            {'id': 'confirm_yes', 'title': 'Sim, confirmar'},
            {'id': 'confirm_no', 'title': 'Cancelar'}
        ]
        
        return {
            'action': 'send_buttons',
            'body': confirmation_text,
            'buttons': buttons
        }
    
    def _handle_confirmation(self, from_number, message, button_id):
        """Handle appointment confirmation"""
        state = self.conversations[from_number]
        
        if button_id == 'confirm_yes' or message == '1':
            # Create appointment in Google Calendar
            try:
                event = self.calendar.create_appointment(
                    patient_name=state['patient_name'],
                    patient_phone=from_number,
                    appointment_type=state['appointment_name'],
                    start_time=state['selected_time'],
                    duration=30
                )
                
                if event:
                    formatted_date = self.calendar.format_date(state['selected_date'])
                    formatted_time = self.calendar.format_time(state['selected_time'])
                    
                    success_message = f"""✅ Agendamento Confirmado!

👤 Paciente: {state['patient_name']}
🏥 Serviço: {state['appointment_