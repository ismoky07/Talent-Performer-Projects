import whois
import requests
import dns.resolver
from textwrap import dedent
from typing import Iterator
from dotenv import load_dotenv
from agno.utils.log import logger
from agno.workflow import Workflow
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response
from tools import check_security_headers, check_common_directories, find_js_urls, check_robots_txt, check_sitemap, check_env_exposure, check_server_header, check_http_redirect, check_github_mentions

load_dotenv()

def extract_domain(url: str) -> str:
    """Extract domain from a full URL."""
    return url.split("//")[-1].split("/")[0]

def get_whois(domain: str) -> str:
    try:
        w = whois.whois(domain)
        return "\n".join(f"{k}: {v}" for k, v in w.items())
    except Exception as e:
        return f"WHOIS lookup failed: {e}"

def get_dns_records(domain: str) -> str:
    try:
        answers = dns.resolver.resolve(domain, 'A')
        return "\n".join(rdata.address for rdata in answers)
    except Exception as e:
        return f"DNS lookup failed: {e}"

def get_http_headers(domain: str) -> str:
    url = f"https://{domain}"
    try:
        response = requests.head(url, timeout=5)
        headers = response.headers
        return "\n".join(f"{k}: {v}" for k, v in headers.items())
    except Exception as e:
        return f"HTTP header fetch failed: {e}"


class OffensiveCybersecurityTester(Workflow):
    recon_agent: Agent = Agent(
        name = 'Recon Agent',
        model=OpenAIChat(id='gpt-4o'),
        description=dedent("""
            Gather detailed information about the target URL to understand its environment and potential vulnerabilities.
            This agent performs passive reconnaissance by collecting public data without interacting aggressively with the target.
        """),
        instructions = dedent("""
            You are a Recon Agent. You will receive reconnaissance data about a target domain.

            Your tasks:
            1. Analyze the WHOIS, DNS, and any available metadata.
            2. Based on patterns (e.g. tech stack, DNS structure, WHOIS info), **categorize** the target:
            - Is it an e-commerce site, blog, SaaS app, API backend, login portal, etc.?
            3. Identify notable or suspicious findings (e.g., short registration, strange DNS, tech used).
            4. Based on the category, **suggest specific types of tests** that could be safely conducted later.
            Example: If it's an e-commerce site, suggest testing cart, search, login, etc.
            
            Your output should include:
            - Target category
            - Key observations
            - List of recommended test types (with short reasons)
            
            Do not make up data. Only use what's in the input.
        """),
    )

    test_agent: Agent = Agent(
        name = 'Test Agent',
        model=OpenAIChat(id='gpt-4o'),
        description=dedent("""
            You are a Test Agent. You will receive an Agent Summary output of recommended tests to conduct on the target domain.
        """),
        instructions = dedent("""
            You are the Tester Agent in an offensive cybersecurity workflow.

            You are equipped with the following **safe and legal tools**:

            1. check_security_headers – Inspect CSP, HSTS, and X-Frame headers.
            2. check_common_directories – Scan for /admin, /login, /config, etc.
            3. find_js_urls – List JS file URLs from the homepage.
            4. check_robots_txt – Look for robots.txt and list contents.
            5. check_sitemap – Look for sitemap.xml and print summary.
            6. check_env_exposure – Check for exposed .env file.
            7. check_server_header – Read the 'Server' HTTP header.
            8. check_http_redirect – Check if HTTP redirects to HTTPS.
            9. check_github_mentions – Provide Google search link for GitHub leaks.

            Your tasks:

            1. Read the **Recon Agent's output** (which includes recon analysis and test recommendations).
            2. Based on those recommendations, **select only the relevant tools** to run.
            3. Perform safe, non-intrusive tests using only those selected tools.
            4. Return a structured response including:

            - ✅ Which tools were used and why (brief reasoning).
            - ❌ Which tools were skipped and why (e.g. “not relevant” or “not recommended”).
            - 📄 A brief summary of findings from each test used.
            - 🔐 A security risk score: Low / Medium / High (based on number and severity of issues found).
            - ➕ (Optional) Suggest other safe checks to run later if helpful.

            Rules:
            - Never run tools unless explicitly recommended by the recon phase.
            - Never test destructively. Only public, passive, and educational analysis is allowed.
        """),
        tools=[check_security_headers, check_common_directories, find_js_urls, check_robots_txt, check_sitemap, check_env_exposure, check_server_header, check_http_redirect, check_github_mentions],
    )

    def run(self, domain: str) -> Iterator[RunResponse]:
        domain = extract_domain(domain)
        whois_info = get_whois(domain)
        dns_records = get_dns_records(domain)
        http_headers = get_http_headers(domain)
        full_context = f"""
        Domain: {domain}
        WHOIS info:
        {whois_info}
        DNS records:
        {dns_records}
        HTTP headers:
        {http_headers}
        """
        logger.info(f'Running Recon for domain: {domain}')
        recon_response: Iterator[RunResponse] = self.recon_agent.run(full_context)
        if recon_response is None or not recon_response.content:
            yield RunResponse(
                run_id=self.run_id,
                content="Sorry, could not get the Recon analysis report.",
            )
            return
        logger.info('Testing the target domain')
        yield from self.test_agent.run(recon_response.content, stream=True)

if __name__ == '__main__':
    from rich.prompt import Prompt

    workflow = OffensiveCybersecurityTester()
    domain = Prompt.ask("Enter the domain to test")
    response: Iterator[RunResponse] = workflow.run(domain=domain)
    pprint_run_response(response, markdown=True)