import sys
from voice_email_logic import send_email_message

def main():
    # If recipient passed as command line argument, use it; otherwise ask or use default
    if len(sys.argv) > 1:
        recipient = sys.argv[1].strip()
    else:
        recipient = input("Enter receiver email address: ").strip()

    if not recipient:
        print("Error: Recipient email address cannot be empty.")
        return

    subject = input("Enter subject [Default: Voice Assistant Test Email]: ").strip()
    if not subject:
        subject = "Voice Assistant Test Email"

    message = input("Enter message body [Default: Hello! This is a test email from the AI Voice Assistance System.]: ").strip()
    if not message:
        message = "Hello! This is a test email from the AI Voice Assistance System."

    print(f"\nSending email to: {recipient} ...")
    result = send_email_message(receiver=recipient, subject=subject, message=message, language="english")

    if result.get("success"):
        print(f"SUCCESS: {result.get('text')}")
    else:
        print(f"FAILED: {result.get('text')} - Error: {result.get('error')}")

if __name__ == "__main__":
    main()
