from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from bytechef_workflow_api import ProjectDefinition, TaskContext


def greet(context: "TaskContext") -> str:
    context.log("info", "Greeting from the embedded catalog")

    return "Hello from the embedded catalog"


def summarize(context: "TaskContext") -> str:
    email = context.input("newEmail")

    summary = f"New email from {email['from']}: {email['subject']}"

    context.log("info", summary)

    return summary


def fetch_emails(context: "TaskContext") -> List[Any]:
    request = context.input().get("request") or {}
    body = request.get("body") or {}

    result = context.component.googleMail.searchEmail(
        {"from": body.get("from"), "maxResults": body.get("maxResults") or 10}, "gmail"
    )

    messages: List[Any] = result.get("messages") or []

    context.log("info", f"Found {len(messages)} emails")

    return messages


def post_to_slack(context: "TaskContext") -> Any:
    email = context.input("newEmail")

    text = f"New email from {email['from']}: {email['subject']}"

    message = context.component.slack.sendChannelMessage({"channel": context.input("channel"), "text": text}, "slack")

    context.log("info", f"Posted to Slack: {text}")

    return message


project: "ProjectDefinition" = {
    "name": "Sample Catalog Code Project Python",
    "version": "1",
    "description": "A sample embedded catalog code project.",
    "workflows": [
        {
            "name": "greetOnRequest",
            "label": "Greet on Request",
            "description": "Answers a request with a greeting.",
            # A request trigger makes the workflow callable through the embedded public endpoints.
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
            # Provisioning binds the trigger to one of the connected user's Gmail connections - for example the
            # one they created when they connected a Gmail integration.
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
                    # A code task's perform calls actions itself, so it declares the connections it uses; the name is
                    # what perform passes to the action. Provisioning binds each one to a connection of the connected
                    # user on the same component.
                    "connections": [{"componentName": "googleMail", "name": "gmail"}],
                    "perform": fetch_emails,
                }
            ],
        },
        {
            "name": "notifySlackOnNewEmail",
            "label": "Notify Slack on New Email",
            "description": "Posts every new email in the connected user's inbox to a Slack channel.",
            # Takes its options from Slack's channel input, so the channel is picked from the workspace's channels.
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
                    # The Gmail trigger needs no declaration, but the task calls Slack itself, so it declares
                    # that connection and passes the name. Provisioning binds it to one of the connected user's
                    # Slack connections.
                    "connections": [{"componentName": "slack", "name": "slack"}],
                    "perform": post_to_slack,
                }
            ],
        },
    ],
}

project
