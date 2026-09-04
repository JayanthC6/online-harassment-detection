class EmailService:
    @staticmethod
    def send_status_update(user_id: str, incident_id: str, action: str, details: dict = None):
        """
        Mock email service to send status updates to users when admins take action on their complaints.
        In a real production system, this would use smtplib, SendGrid, SES, etc.
        """
        email_address = f"{user_id}@example.com" if user_id and user_id != "unknown" else "anonymous@example.com"
        
        subject = f"Update on your complaint (ID: {incident_id[-6:] if incident_id else 'unknown'})"
        
        if action == "dismiss":
            body = f"Hello {user_id},\n\nYour complaint has been reviewed and dismissed by our administration team. No further action will be taken at this time."
        elif action == "override":
            new_label = details.get("new_label", "updated") if details else "updated"
            body = f"Hello {user_id},\n\nYour complaint's classification has been updated to '{new_label}' by our administration team. We are continuing to monitor the situation."
        else:
            body = f"Hello {user_id},\n\nThere has been an update regarding your complaint. Action taken: {action}."
            
        print("\n" + "="*50)
        print(f"📧 EMAIL DISPATCHED")
        print(f"To: {email_address}")
        print(f"Subject: {subject}")
        print("-" * 50)
        print(body)
        print("="*50 + "\n")
