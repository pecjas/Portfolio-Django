from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Education, Job, JobDetail, Project, Skill


class PageSmokeTests(TestCase):
    """Every page renders, and renders the markup the layout depends on."""

    @classmethod
    def setUpTestData(cls):
        job = Job.objects.create(
            employer="Esker Inc",
            title="Solution Architect",
            startDate=date(2025, 4, 1))
        JobDetail.objects.create(relatedJob=job, content="Built things.")

        Education.objects.create(
            graduationDate=date(2017, 5, 1),
            school="University",
            degree="BBA",
            GPA="3.500",
            additionalInfo="Dean's list")

        Skill.objects.create(skill="Python")

        cls.project = Project.objects.create(
            title="Portfolio Website",
            briefDescription="The site you are looking at.",
            content="Built with Django.",
            language="Python, HTML",
            githubLink="https://github.com/pecjas/Portfolio-Django")

    def assertWellFormedPage(self, response):
        html = response.content.decode()
        self.assertTrue(html.lstrip().startswith("<!DOCTYPE html>"))
        self.assertIn('<html lang="en">', html)
        self.assertIn('name="viewport"', html)
        self.assertIn("<h1", html)

    def test_home_page(self):
        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, 200)
        self.assertWellFormedPage(response)
        self.assertContains(response, "Solution Architect")

    def test_portfolio_page(self):
        response = self.client.get(reverse("main:portfolio"))
        self.assertEqual(response.status_code, 200)
        self.assertWellFormedPage(response)
        self.assertContains(response, "Portfolio Website")

    def test_contact_page(self):
        response = self.client.get(reverse("main:contact"))
        self.assertEqual(response.status_code, 200)
        self.assertWellFormedPage(response)

    def test_project_page(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertWellFormedPage(response)
        self.assertContains(response, "Built with Django.")

    def test_pages_have_distinct_titles(self):
        titles = set()

        for url in [
            reverse("main:index"),
            reverse("main:portfolio"),
            reverse("main:contact"),
            self.project.get_absolute_url(),
        ]:
            response = self.client.get(url)
            titles.add(response.context["page_title"])

        self.assertEqual(len(titles), 4)

    def test_stylesheet_url_is_versioned(self):
        """A cached stylesheet at an unchanged URL renders new markup without its rules."""
        response = self.client.get(reverse("main:index"))

        self.assertRegex(
            response.content.decode(),
            r'href="/static/main/css/materialize\.css\?v=\d+"')

    def test_active_collapsible_section_opens_without_javascript(self):
        response = self.client.get(reverse("main:index"))

        self.assertContains(response, '<li class="active">')

    def test_unknown_project_returns_404(self):
        response = self.client.get(reverse("main:project", kwargs={"slug": "does-not-exist"}))
        self.assertEqual(response.status_code, 404)


class QueryCountTests(TestCase):
    """Guards against a query per row creeping back into the list views."""

    @classmethod
    def setUpTestData(cls):
        for n in range(6):
            job = Job.objects.create(
                employer=f"Employer {n}",
                title=f"Title {n}",
                startDate=date(2020 + n % 5, 1, 1))

            for d in range(4):
                JobDetail.objects.create(relatedJob=job, content=f"Detail {n}-{d}")

        for n in range(8):
            Project.objects.create(
                title=f"Project {n}",
                briefDescription="x",
                content="y",
                language="Python")

    def test_home_page_query_count_does_not_grow_with_jobs(self):
        with self.assertNumQueries(4):
            self.client.get(reverse("main:index"))

    def test_portfolio_page_query_count_does_not_grow_with_projects(self):
        with self.assertNumQueries(2):
            self.client.get(reverse("main:portfolio"))


class ProjectSlugTests(TestCase):

    def test_slug_is_generated_from_title(self):
        project = Project.objects.create(
            title="Referral ETL Process",
            briefDescription="x",
            content="y")

        self.assertEqual(project.slug, "referral-etl-process")

    def test_duplicate_titles_get_distinct_slugs(self):
        first = Project.objects.create(title="Test", briefDescription="x", content="y")
        second = Project.objects.create(title="Test", briefDescription="x", content="y")

        self.assertEqual(first.slug, "test")
        self.assertEqual(second.slug, "test-2")

    def test_explicit_slug_is_kept(self):
        project = Project.objects.create(
            title="Anything",
            slug="chosen-by-hand",
            briefDescription="x",
            content="y")

        self.assertEqual(project.slug, "chosen-by-hand")


class LegacyProjectUrlTests(TestCase):

    def test_old_query_string_url_redirects_to_slug(self):
        project = Project.objects.create(
            title="Portfolio Website",
            briefDescription="x",
            content="y")

        response = self.client.get("/project/", {"id": "Portfolio Website"})

        self.assertRedirects(response, project.get_absolute_url(), status_code=301)

    def test_unknown_title_returns_404(self):
        response = self.client.get("/project/", {"id": "No Such Project"})

        self.assertEqual(response.status_code, 404)

    def test_missing_id_returns_404(self):
        response = self.client.get("/project/")

        self.assertEqual(response.status_code, 404)
