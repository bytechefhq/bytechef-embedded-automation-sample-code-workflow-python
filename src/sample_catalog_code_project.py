from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bytechef_workflow_api import ProjectDefinition, TaskContext


def greet(context: "TaskContext") -> str:
    context.log("info", "Greeting from the embedded catalog")

    return "Hello from the embedded catalog"


project: "ProjectDefinition" = {
    "name": "Sample Catalog Code Project Python",
    "version": "1",
    "description": "A sample embedded catalog code project.",
    "workflows": [
        {
            "name": "greetOnRequest",
            "label": "Greet on Request",
            "description": "Answers a request with a greeting.",
            # A catalog workflow is only reachable through the embedded public endpoints when it declares a
            # request trigger or an app-event trigger. Without one the import still succeeds, with a warning.
            "triggers": [{"name": "request", "type": "request/v1/autoRespondWithHTTP200"}],
            "outputs": [{"name": "greeting", "task": "greet"}],
            "tasks": [
                {
                    "name": "greet",
                    "label": "Greet",
                    "perform": greet,
                }
            ],
        }
    ],
}

project
