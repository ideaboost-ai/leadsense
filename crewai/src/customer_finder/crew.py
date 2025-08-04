from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from crewai_tools import ScrapeWebsiteTool
from typing import List

@CrewBase
class CustomerFinder():
    """CustomerFinder crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def customer_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['customer_finder'],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def customer_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['customer_researcher'],
            verbose=True,
            tools=[SerperDevTool(), ScrapeWebsiteTool(website_url='https://www.ideaboost.ai')]
        )

    @task
    def customer_search_task(self) -> Task:
        return Task(
            config=self.tasks_config['customer_search_task'],
            output_file='output/customers.md'
        )

    @task
    def customer_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['customer_research_task'],
            output_file='output/report.md'
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the CustomerFinder crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

