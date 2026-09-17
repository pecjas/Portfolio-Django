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
            r'href="/static/main/css/app\.css\?v=\d+"')

    def test_default_accordion_section_opens_without_javascript(self):
        """It is a native <details open>, so it is expanded before any JS runs."""
        response = self.client.get(reverse("main:index"))

        self.assertContains(response, '<details class="accordion__item" open>')

    def test_theme_preference_is_applied_before_first_paint(self):
        """The inline script must be in <head>, ahead of <body>, and not deferred.

        A deferred or body-end script would run after the first paint, flashing
        the light palette at anyone who chose dark.
        """
        html = self.client.get(reverse("main:index")).content.decode()

        script_at = html.index('localStorage.getItem("theme")')
        self.assertLess(script_at, html.index("<body>"))

        opening_tag = html.rindex("<script", 0, script_at)
        tag = html[opening_tag:html.index(">", opening_tag)]
        self.assertNotIn("defer", tag)
        self.assertNotIn("async", tag)
        self.assertNotIn("src=", tag)

    def test_theme_toggle_is_hidden_until_scripted(self):
        """It does nothing without JS, so it should not be offered without JS."""
        html = self.client.get(reverse("main:index")).content.decode()

        self.assertIn("data-theme-toggle", html)
        toggle_at = html.index("data-theme-toggle")
        tag = html[html.rindex("<button", 0, toggle_at):html.index(">", toggle_at)]
        self.assertIn("hidden", tag)

    def test_no_framework_assets_remain(self):
        response = self.client.get(reverse("main:index"))
        html = response.content.decode()

        for gone in ["materialize", "jquery", "fonts.googleapis.com"]:
            self.assertNotIn(gone, html.lower())

    def test_templates_emit_no_literal_template_comments(self):
        """Django's {# #} is single-line; a multi-line one renders verbatim."""
        for url in [
            reverse("main:index"),
            reverse("main:portfolio"),
            reverse("main:contact"),
        ]:
            with self.subTest(url=url):
                self.assertNotIn("{#", self.client.get(url).content.decode())

    def test_filter_controls_degrade_without_javascript(self):
        """Filtering is a JS enhancement, so its controls must not be offered
        as working UI in a response that JS has not touched yet."""
        html = self.client.get(reverse("main:portfolio")).content.decode()

        for element_id in ["filter-chips", "filter-empty", "filter-clear"]:
            with self.subTest(element=element_id):
                at = html.index('id="%s"' % element_id)
                tag = html[html.rindex("<", 0, at):html.index(">", at)]
                self.assertIn("hidden", tag)

        # Every project is present and linked regardless.
        self.assertEqual(html.count('class="card project-card'), Project.objects.count())

    def test_filter_menu_buttons_carry_their_display_labels(self):
        """The chips read their labels off these buttons, so C_Sharp must render
        as its display name rather than the filter key."""
        html = self.client.get(reverse("main:portfolio")).content.decode()

        self.assertIn('data-filter-value="C_Sharp"', html)
        self.assertRegex(html, r'data-filter-value="C_Sharp"[^>]*>\s*C#')

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


class ProjectKindTests(TestCase):
    """Personal/Professional is now an explicit field, not an inference."""

    def test_kind_reads_from_the_field_not_the_github_link(self):
        professional_with_source = Project.objects.create(
            title="Open sourced at work",
            briefDescription="x",
            content="y",
            githubLink="https://github.com/example/repo",
            is_personal=False)

        personal_without_source = Project.objects.create(
            title="Private side project",
            briefDescription="x",
            content="y",
            is_personal=True)

        # Both combinations were impossible to express under the old heuristic.
        self.assertEqual(professional_with_source.kind, "Professional")
        self.assertEqual(personal_without_source.kind, "Personal")

    def test_portfolio_page_renders_the_field(self):
        Project.objects.create(
            title="Work thing",
            briefDescription="x",
            content="y",
            githubLink="https://github.com/example/repo",
            is_personal=False)

        html = self.client.get(reverse("main:portfolio")).content.decode()

        self.assertIn('data-filter-personal-status="Professional"', html)
        self.assertIn("project-card--professional", html)


class OutboundLinkTests(TestCase):
    """Links that leave the site open in a new tab, safely and audibly."""

    def test_profile_links_open_in_a_new_tab(self):
        with self.settings(LINKEDIN_URL="https://www.linkedin.com/in/jason-j-peck/"):
            html = self.client.get(reverse("main:index")).content.decode()

        for host in ["github.com/pecjas", "linkedin.com/in/"]:
            with self.subTest(host=host):
                at = html.index(host)
                tag = html[html.rindex("<a", 0, at):html.index(">", at)]
                self.assertIn('target="_blank"', tag)

    def test_every_new_tab_link_sets_rel_noopener(self):
        """Without it, the opened page can reach back via window.opener."""
        import re

        with self.settings(LINKEDIN_URL="https://www.linkedin.com/in/jason-j-peck/"):
            pages = [
                self.client.get(reverse("main:index")).content.decode(),
                self.client.get(reverse("main:portfolio")).content.decode(),
            ]

        for html in pages:
            for tag in re.findall(r"<a[^>]*target=\"_blank\"[^>]*>", html):
                with self.subTest(tag=tag[:70]):
                    self.assertIn("noopener", tag)

    def test_new_tab_links_announce_themselves(self):
        """Opening a new tab unannounced is disorienting for screen reader users."""
        with self.settings(LINKEDIN_URL="https://www.linkedin.com/in/jason-j-peck/"):
            html = self.client.get(reverse("main:index")).content.decode()

        self.assertEqual(html.count("(opens in a new tab)"), 2)

    def test_internal_links_stay_in_the_same_tab(self):
        html = self.client.get(reverse("main:index")).content.decode()

        for internal in [reverse("main:portfolio"), reverse("main:contact")]:
            at = html.index('href="%s"' % internal)
            tag = html[html.rindex("<a", 0, at):html.index(">", at)]
            self.assertNotIn("target=", tag)


class OptionalAssetTests(TestCase):
    """A CV link should appear only once there is a CV to link to."""

    CV = "main/files/jason-peck-resume.pdf"

    def test_link_presence_tracks_the_file(self):
        """Whether the CV link renders should follow whether the file is there,
        so this holds both before and after the PDF is added."""
        from django.contrib.staticfiles import finders

        cv_exists = finders.find(self.CV) is not None

        for url in [reverse("main:index"), reverse("main:contact")]:
            with self.subTest(url=url, cv_exists=cv_exists):
                html = self.client.get(url).content.decode()
                self.assertEqual("jason-peck-resume.pdf" in html, cv_exists)

    def test_link_is_served_from_static_not_the_app_root(self):
        """A file dropped at main/files/ rather than main/static/main/files/ is
        invisible to the staticfiles finders, which is how it was first missed."""
        from django.contrib.staticfiles import finders

        found = finders.find(self.CV)

        if found is None:
            self.skipTest("no CV present in this checkout")

        self.assertIn("static", found.replace("\\", "/").lower())

    def test_static_if_exists_returns_empty_for_missing_file(self):
        from main.templatetags.versioned_static import static_if_exists

        self.assertEqual(static_if_exists("main/files/definitely-not-here.pdf"), "")
        self.assertNotEqual(static_if_exists("main/css/app.css"), "")


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
