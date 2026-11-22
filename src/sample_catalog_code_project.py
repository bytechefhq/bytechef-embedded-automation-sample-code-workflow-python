from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from bytechef_workflow_api import ProjectDefinition, TaskContext


def greet(input: Dict[str, Any], context: "TaskContext") -> str:
    context.log("info", "Greeting from the embedded catalog")

    return "Hello from the embedded catalog"


def summarize(input: Dict[str, Any], context: "TaskContext") -> str:
    email = input["newEmail"]

    summary = f"New email from {email['from']}: {email['subject']}"

    context.log("info", summary)

    return summary


def fetch_emails(input: Dict[str, Any], context: "TaskContext") -> List[Any]:
    request = input.get("request") or {}
    body = request.get("body") or {}

    result = context.component.googleMail.searchEmail(
        {"from": body.get("from"), "maxResults": body.get("maxResults") or 10}, "gmail"
    )

    messages: List[Any] = result.get("messages") or []

    context.log("info", f"Found {len(messages)} emails")

    return messages


def post_to_slack(input: Dict[str, Any], context: "TaskContext") -> Any:
    email = input["newEmail"]

    text = f"New email from {email['from']}: {email['subject']}"

    message = context.component.slack.sendChannelMessage({"channel": input.get("channel"), "text": text}, "slack")

    context.log("info", f"Posted to Slack: {text}")

    return message


def describe(input: Dict[str, Any], context: "TaskContext") -> Dict[str, Any]:
    email = input["newEmail"]

    context.log("info", f"Describing email {email['id']}")

    return {"sender": email["from"], "subject": email["subject"]}


project: "ProjectDefinition" = {
    "name": "Sample Catalog Code Project Python",
    "version": "1",
    "description": "A sample embedded catalog code project.",
    "workflows": [
        {
            "name": "greetOnRequest",
            "label": "Greet on Request",
            "description": "Answers a request with a greeting.",
            "triggers": [{"name": "request", "type": "request/v1/autoRespondWithHTTP200"}],
            "outputs": [{"name": "greeting", "task": "greet"}],
            "tasks": [
                {
                    "name": "greet",
                    "label": "Greet",
                    "perform": greet,
                }
            ],
        },
        {
            "name": "summarizeNewEmail",
            "label": "Summarize New Email",
            "description": "Runs for every new email in the connected user's inbox and logs who sent it.",
            "triggers": [
                {"name": "newEmail", "type": "googleMail/v1/newEmailPolling", "parameters": {"format": "SIMPLE"}}
            ],
            "outputs": [{"name": "summary", "task": "summarize"}],
            "tasks": [
                {
                    "name": "summarize",
                    "label": "Summarize",
                    "perform": summarize,
                }
            ],
        },
        {
            "name": "fetchRecentEmails",
            "label": "Fetch Recent Emails",
            "description": "Returns the connected user's most recent emails, optionally only those from one sender.",
            "triggers": [{"name": "request", "type": "request/v1/awaitWorkflowAndRespond"}],
            "outputs": [{"name": "emails", "task": "fetchEmails"}],
            "tasks": [
                {
                    "name": "fetchEmails",
                    "label": "Fetch Emails",
                    "connections": [{"componentName": "googleMail", "name": "gmail"}],
                    "perform": fetch_emails,
                }
            ],
        },
        {
            "name": "notifySlackOnNewEmail",
            "label": "Notify Slack on New Email",
            "description": "Posts every new email in the connected user's inbox to a Slack channel.",
            "inputs": [
                {
                    "name": "channel",
                    "label": "Slack Channel",
                    "type": "STRING",
                    "required": True,
                    "componentName": "slack",
                    "componentVersion": 1,
                    "groupName": "channel",
                }
            ],
            "triggers": [
                {"name": "newEmail", "type": "googleMail/v1/newEmailPolling", "parameters": {"format": "SIMPLE"}}
            ],
            "outputs": [{"name": "message", "task": "postToSlack"}],
            "tasks": [
                {
                    "name": "postToSlack",
                    "label": "Post to Slack",
                    "description": "Posts the sender and subject with the Slack Send Channel Message action.",
                    "connections": [{"componentName": "slack", "name": "slack"}],
                    "perform": post_to_slack,
                }
            ],
        },
        {
            "name": "logNewEmailSender",
            "label": "Log New Email Sender",
            "description": (
                "Logs the sender of every new email in the connected user's inbox with the Logger component."
            ),
            "triggers": [
                {"name": "newEmail", "type": "googleMail/v1/newEmailPolling", "parameters": {"format": "SIMPLE"}}
            ],
            "tasks": [
                {"name": "describe", "label": "Describe", "perform": describe},
                {
                    "name": "logSender",
                    "label": "Log Sender",
                    "description": "Writes the sender and subject to the execution log with the Logger Info action.",
                    "type": "logger/v1/info",
                    "parameters": {"text": "New email from ${describe.sender}: ${describe.subject}"},
                },
            ],
        },
    ],
}

project
