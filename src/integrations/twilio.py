"""
Twilio wrapper class for managing inbound and outbound calls.

Abstracts Twilio SDK functionality for:
- Handling inbound calls from patients
- Making outbound reminder calls
- Sending SMS confirmations
"""

from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from src import config
from colorama import Fore, init

init(autoreset=True)


class TwilioCallError(Exception):
    """Raised when Twilio operations fail"""
    pass


class TwilioWrapper:
    """
    Wrapper class for Twilio operations.

    Manages:
    - Inbound call routing
    - Outbound call initiation
    - SMS sending
    - Call status monitoring
    """

    def __init__(self):
        """Initialize Twilio client with credentials from config"""
        try:
            self.client = Client(
                config.TWILIO_ACCOUNT_SID,
                config.TWILIO_AUTH_TOKEN
            )
            self.phone_number = config.TWILIO_PHONE_NUMBER
            print(f"{Fore.GREEN}✅ Twilio client initialized")
        except Exception as e:
            error_msg = f"Failed to initialize Twilio client: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}")
            raise TwilioCallError(error_msg)

    # ========================================================================
    # INBOUND CALL HANDLING
    # ========================================================================

    def handle_inbound_call(self, from_number: str, to_number: str) -> VoiceResponse:
        """
        Handle incoming call from patient.

        This is called by Twilio webhook when patient calls in.
        Returns TwiML that routes to ElevenLabs agent.

        Args:
            from_number: Caller's phone number
            to_number: Called-to phone number (our Twilio number)

        Returns:
            VoiceResponse: TwiML instructions for Twilio
        """
        response = VoiceResponse()

        # Route to ElevenLabs ConvAI webhook
        # The webhook URL is configured in ElevenLabs dashboard
        # This <Connect> statement routes the call to the agent
        response.connect(
            stream_params={
                "url": config.WEBHOOK_URL,
                "name": f"Patient call from {from_number}"
            }
        )

        if config.DEBUG:
            print(f"{Fore.CYAN}[DEBUG] Inbound call from {from_number} → {to_number}")

        return response

    # ========================================================================
    # OUTBOUND CALL HANDLING
    # ========================================================================

    def make_outbound_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        twiml_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call to a patient.

        Used for appointment reminders.

        Args:
            to_number: Recipient's phone number (E.164 format)
            from_number: Caller ID (defaults to TWILIO_PHONE_NUMBER)
            twiml_url: URL to TwiML instructions for the call
            **kwargs: Additional Twilio Call API parameters

        Returns:
            dict: Call SID and status

        Raises:
            TwilioCallError: If call initiation fails
        """
        if not from_number:
            from_number = self.phone_number

        try:
            call = self.client.calls.create(
                to=to_number,
                from_=from_number,
                url=twiml_url or config.WEBHOOK_URL,
                timeout=config.TWILIO_API_TIMEOUT_SECONDS,
                **kwargs
            )

            if config.DEBUG:
                print(f"{Fore.CYAN}[DEBUG] Outbound call initiated: {call.sid}")

            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
                "to": to_number,
                "from": from_number
            }

        except Exception as e:
            error_msg = f"Failed to initiate outbound call to {to_number}: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}")
            raise TwilioCallError(error_msg)

    # ========================================================================
    # CALL MONITORING
    # ========================================================================

    def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """
        Get current status of a call.

        Args:
            call_sid: Twilio Call SID

        Returns:
            dict: Call status information

        Raises:
            TwilioCallError: If call lookup fails
        """
        try:
            call = self.client.calls(call_sid).fetch()

            return {
                "call_sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "price": call.price,
                "to": call.to,
                "from": call.from_,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "direction": call.direction
            }

        except Exception as e:
            error_msg = f"Failed to fetch call status for {call_sid}: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}")
            raise TwilioCallError(error_msg)

    def list_calls(self, limit: int = 10, **kwargs) -> list:
        """
        List recent calls.

        Args:
            limit: Number of calls to return
            **kwargs: Additional filter parameters

        Returns:
            list: Call records

        Raises:
            TwilioCallError: If call listing fails
        """
        try:
            calls = self.client.calls.list(limit=limit, **kwargs)
            return [
                {
                    "call_sid": call.sid,
                    "status": call.status,
                    "duration": call.duration,
                    "to": call.to,
                    "from": call.from_,
                    "direction": call.direction,
                    "start_time": call.start_time
                }
                for call in calls
            ]

        except Exception as e:
            error_msg = f"Failed to list calls: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}")
            raise TwilioCallError(error_msg)

    # ========================================================================
    # SMS HANDLING
    # ========================================================================

    def send_sms(
        self,
        to_number: str,
        message: str,
        from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS confirmation to patient.

        Args:
            to_number: Recipient phone number (E.164 format)
            message: SMS message body
            from_number: Sender phone number (defaults to TWILIO_PHONE_NUMBER)

        Returns:
            dict: Message SID and status

        Raises:
            TwilioCallError: If SMS sending fails
        """
        if not config.ENABLE_SMS_CONFIRMATIONS:
            if config.DEBUG:
                print(f"{Fore.CYAN}[DEBUG] SMS confirmations disabled, skipping")
            return {"success": True, "skipped": True, "reason": "SMS disabled"}

        if not from_number:
            from_number = self.phone_number

        try:
            sms = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )

            if config.DEBUG:
                print(f"{Fore.CYAN}[DEBUG] SMS sent: {sms.sid}")

            return {
                "success": True,
                "message_sid": sms.sid,
                "status": sms.status,
                "to": to_number,
                "from": from_number
            }

        except Exception as e:
            error_msg = f"Failed to send SMS to {to_number}: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}")
            raise TwilioCallError(error_msg)

    # ========================================================================
    # CALL TERMINATION
    # ========================================================================

    def hang_up_call(self, call_sid: str) -> Dict[str, Any]:
        """
        Terminate an active call.

        Args:
            call_sid: Twilio Call SID

        Returns:
            dict: Updated call status

        Raises:
            TwilioCallError: If termination fails
        """
        try:
            call = self.client.calls(call_sid).update(status="completed")

            if config.DEBUG:
                print(f"{Fore.CYAN}[DEBUG] Call terminated: {call_sid}")

            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status
            }

        except Exception as e:
            error_msg = f"Failed to terminate call {call_sid}: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}")
            raise TwilioCallError(error_msg)

    # ========================================================================
    # TWIML HELPERS
    # ========================================================================

    @staticmethod
    def create_gather_response(
        prompt: str,
        num_digits: int = 1,
        finish_on_key: str = "#"
    ) -> VoiceResponse:
        """
        Create TwiML for gathering DTMF input (IVR).

        Args:
            prompt: Voice prompt to play
            num_digits: Number of digits to collect
            finish_on_key: Key that ends input collection

        Returns:
            VoiceResponse: TwiML for gathering input
        """
        response = VoiceResponse()
        response.gather(
            num_digits=num_digits,
            finish_on_key=finish_on_key
        ).say(prompt)
        return response

    @staticmethod
    def create_say_response(message: str, language: str = "en") -> VoiceResponse:
        """
        Create TwiML to say a message.

        Args:
            message: Message to speak
            language: Language code (default: "en")

        Returns:
            VoiceResponse: TwiML for speaking message
        """
        response = VoiceResponse()
        response.say(message, language=language)
        return response
