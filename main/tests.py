import re
from datetime import date
from pathlib import Path

from django.test import TestCase
from django.urls import reverse

from .models import Education, Job, Project, Skill


class PageSmokeTests(TestCase):
    """Every page renders, and renders the markup the layout depends on."""

    @classmethod
    def setUpTestData(cls):
        Job.objects.create(
            employer="Esker Inc",
            title="Solution Architect",
            startDate=date(2025, 4, 1),
            responsibilities="Built things.")

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
        # Menus now list only languages a project uses, so C# has to be in use
        # for its button to exist at all.
        Project.objects.create(title="Audit Tool", briefDescription="b",
                               content="c", language="C#")
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
            Job.objects.create(
                employer=f"Employer {n}",
                title=f"Title {n}",
                startDate=date(2020 + n % 5, 1, 1),
                responsibilities="\n".join(f"Detail {n}-{d}" for d in range(4)))

        for n in range(8):
            Project.objects.create(
                title=f"Project {n}",
                briefDescription="x",
                content="y",
                language="Python")

    def test_home_page_query_count_does_not_grow_with_jobs(self):
        """Constant, not merely small: the skills section counts projects per
        skill, which is the kind of thing that turns into a query per row.

        Four rather than five since the bullets moved onto Job: there is no
        longer a second table to prefetch.
        """
        capability = Skill.objects.get(skill="Systems Integration")
        for project in Project.objects.all():
            project.skills.add(capability)

        with self.assertNumQueries(4):
            self.client.get(reverse("main:index"))

        for n in range(6):
            Job.objects.create(employer=f"Extra {n}", title=f"T{n}",
                               startDate=date(2015, 1, 1),
                               responsibilities="d")

            extra = Project.objects.create(
                title=f"Extra project {n}", briefDescription="x", content="y",
                language="Python")
            extra.skills.add(capability)

        Skill.objects.create(skill="Kubernetes", category=Skill.Category.PLATFORM)

        with self.assertNumQueries(4):
            self.client.get(reverse("main:index"))

    def test_portfolio_page_query_count_does_not_grow_with_projects(self):
        """Asserts a *constant*, not merely a small number: the count has to be
        identical whether the page renders 8 projects or 16, with capabilities
        attached so the skills prefetch is actually exercised."""
        capability = Skill.objects.get(skill="Systems Integration")
        for project in Project.objects.all():
            project.skills.add(capability)

        with self.assertNumQueries(4):
            self.client.get(reverse("main:portfolio"))

        for n in range(8):
            extra = Project.objects.create(
                title=f"Extra {n}", briefDescription="x", content="y",
                language="Python")
            extra.skills.add(capability)

        with self.assertNumQueries(4):
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


class ErrorPageTests(TestCase):
    """Django substitutes its own debug 404 while DEBUG is True, so the styled
    template only ever renders in production. That makes it easy to break
    without noticing."""

    def test_404_uses_the_site_template(self):
        with self.settings(DEBUG=False, ALLOWED_HOSTS=["testserver"]):
            response = self.client.get("/no-such-page/")

        self.assertEqual(response.status_code, 404)
        self.assertIn("404.html", [t.name for t in response.templates])
        self.assertIn("main/header.html", [t.name for t in response.templates])

    def test_preview_route_renders_the_error_templates(self):
        for code in (404, 500):
            with self.subTest(code=code):
                with self.settings(DEBUG=True):
                    response = self.client.get(
                        reverse("main:preview_error_page", args=[code]))

                self.assertEqual(response.status_code, code)
                self.assertIn(f"{code}.html", [t.name for t in response.templates])

    def test_preview_route_is_dead_in_production(self):
        """The pattern is always registered, so the view itself has to refuse."""
        with self.settings(DEBUG=False, ALLOWED_HOSTS=["testserver"]):
            response = self.client.get(
                reverse("main:preview_error_page", args=[404]))

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("500.html", [t.name for t in response.templates])


class SocialCardTests(TestCase):
    """Every referenced image must actually resolve.

    og:image pointed at jasonpeck.png for a while after that file was replaced
    by a .jpg, so link previews were fetching a 404 and nobody noticed — the
    tag is invisible on the page itself.
    """

    def _meta(self, html, attr, value):
        match = re.search(
            r'<meta [^>]*%s="%s"[^>]*content="([^"]*)"' % (attr, re.escape(value)),
            html)
        self.assertIsNotNone(match, f"no meta {attr}={value}")
        return match.group(1)

    def test_share_images_resolve_to_a_real_file(self):
        from django.contrib.staticfiles import finders

        html = self.client.get(reverse("main:index")).content.decode()

        for attr, value in [("property", "og:image"), ("name", "twitter:image")]:
            with self.subTest(tag=value):
                url = self._meta(html, attr, value)
                path = url.split("/static/", 1)[1].split("?")[0]
                self.assertIsNotNone(
                    finders.find(path), f"{value} points at missing {path}")

    def test_share_image_is_landscape_for_link_previews(self):
        """A portrait crop gets letterboxed by LinkedIn and Slack. The declared
        dimensions must match the file, or the preview reserves the wrong box."""
        from django.contrib.staticfiles import finders
        from PIL import Image

        html = self.client.get(reverse("main:index")).content.decode()

        declared = (int(self._meta(html, "property", "og:image:width")),
                    int(self._meta(html, "property", "og:image:height")))

        url = self._meta(html, "property", "og:image")
        path = url.split("/static/", 1)[1].split("?")[0]

        with Image.open(finders.find(path)) as img:
            self.assertEqual(img.size, declared)

        ratio = declared[0] / declared[1]
        self.assertGreater(ratio, 1.5, "share image should be landscape")


class SkillTaxonomyTests(TestCase):
    """Phase 1 of the capability plan: the vocabulary and its slugs."""

    def test_slug_is_generated_from_the_name(self):
        # Not a name the seed migration already created, or this would collide
        # and legitimately come back as "-2".
        skill = Skill.objects.create(skill="Message Queues")

        self.assertEqual(skill.slug, "message-queues")

    def test_symbols_are_spelled_out_rather_than_stripped(self):
        """Bare slugify turns both "C#" and "C++" into "c", which collides and
        reads as nothing in a URL."""
        for name, expected in [("C#", "c-sharp"),
                               ("C++", "c-plus-plus"),
                               ("Batch & Stream", "batch-and-stream")]:
            with self.subTest(name=name):
                self.assertEqual(Skill.objects.create(skill=name).slug, expected)

    def test_duplicate_names_get_distinct_slugs(self):
        first = Skill.objects.create(skill="Integration")
        second = Skill.objects.create(skill="Integration")

        self.assertEqual(first.slug, "integration")
        self.assertEqual(second.slug, "integration-2")

    def test_explicit_slug_is_kept(self):
        skill = Skill.objects.create(skill="Healthcare", slug="hl7")

        self.assertEqual(skill.slug, "hl7")

    def test_leadership_skills_are_seeded_as_practices(self):
        """Selectable per project and rendered on the card, but not part of the
        capability axis -- that answers what kind of work a project is, and
        stays small enough to be worth filtering on."""
        for name in ("Project Management", "Leadership"):
            with self.subTest(name=name):
                skill = Skill.objects.get(skill=name)

                self.assertEqual(skill.category, Skill.Category.PRACTICE)
                self.assertFalse(skill.is_capability)

    def test_practice_skills_render_on_a_card(self):
        project = Project.objects.create(
            title="Delivery Programme", briefDescription="b", content="c",
            language="Python")
        project.skills.add(Skill.objects.get(skill="Project Management"),
                           Skill.objects.get(skill="Leadership"))

        html = self.client.get(reverse("main:portfolio")).content.decode()

        self.assertIn("Project Management", html)
        self.assertIn("Leadership", html)

    def test_capability_vocabulary_is_seeded(self):
        """The migration creates these so the axis stays a small, fixed set."""
        seeded = Skill.objects.filter(category=Skill.Category.CAPABILITY)

        self.assertIn("Systems Integration", [s.skill for s in seeded])
        self.assertGreaterEqual(seeded.count(), 6)

    def test_only_capabilities_report_as_capabilities(self):
        capability = Skill.objects.create(
            skill="Data Pipelines", category=Skill.Category.CAPABILITY)
        language = Skill.objects.create(
            skill="Rust", category=Skill.Category.LANGUAGE)

        self.assertTrue(capability.is_capability)
        self.assertFalse(language.is_capability)


class ProjectCapabilityTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            title="Referral Pipeline", briefDescription="b", content="c",
            language="Python")

        self.capability = Skill.objects.create(
            skill="Data Movement", category=Skill.Category.CAPABILITY)
        self.platform = Skill.objects.create(
            skill="Airflow", category=Skill.Category.PLATFORM)
        self.language = Skill.objects.create(
            skill="Rust", category=Skill.Category.LANGUAGE)

    def test_capabilities_returns_only_capability_skills(self):
        self.project.skills.set([self.capability, self.platform, self.language])

        self.assertEqual([s.skill for s in self.project.capabilities],
                         ["Data Movement"])

    def test_supporting_skills_excludes_capabilities_and_languages(self):
        """Languages render from Project.language; capabilities get their own
        prominent treatment. This is everything else."""
        self.project.skills.set([self.capability, self.platform, self.language])

        self.assertEqual([s.skill for s in self.project.supporting_skills],
                         ["Airflow"])

    def test_a_project_with_no_skills_has_no_capabilities(self):
        """The state every project is in until content is entered. Phase 2's
        templates must tolerate it."""
        self.assertEqual(self.project.capabilities, [])
        self.assertEqual(self.project.supporting_skills, [])

    def test_new_fields_default_to_absent(self):
        self.assertFalse(self.project.featured)
        self.assertIsNone(self.project.startDate)
        self.assertIsNone(self.project.endDate)

    def test_typescript_is_a_selectable_language(self):
        """Absent before Phase 1, despite four years of shipping it."""
        self.assertIn("TypeScript", Project.ProgramLanguage.values)


class EmptyTaxonomyTests(TestCase):
    """Code lands before content, so every page must render correctly while no
    project has a capability assigned."""

    def setUp(self):
        Project.objects.create(title="Only Project", briefDescription="b",
                               content="c", language="Python")

    def test_portfolio_page_renders_with_no_capabilities_assigned(self):
        response = self.client.get(reverse("main:portfolio"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only Project")

    def test_home_page_renders_with_no_capabilities_assigned(self):
        self.assertEqual(self.client.get(reverse("main:index")).status_code, 200)

    def test_project_page_renders_with_no_capabilities_assigned(self):
        project = Project.objects.get(title="Only Project")

        self.assertEqual(self.client.get(project.get_absolute_url()).status_code, 200)


class AdminContentEntryTests(TestCase):
    """The admin is the only way capability content gets entered, so a
    misconfigured ModelAdmin is a blocker rather than a cosmetic problem."""

    def setUp(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("editor", "editor@example.com", "pw")
        self.client.force_login(User.objects.get(username="editor"))

        self.project = Project.objects.create(
            title="Referral Pipeline", briefDescription="b", content="c",
            language="Python")

    def test_project_form_offers_the_skill_picker(self):
        response = self.client.get(
            reverse("admin:main_project_change", args=[self.project.pk]))

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for field in ("skills", "featured", "startDate", "endDate"):
            with self.subTest(field=field):
                self.assertIn(field, html)

    def test_project_list_renders_with_no_capabilities_assigned(self):
        """capability_list has to cope with an empty set, which is every row
        until content is entered."""
        response = self.client.get(reverse("admin:main_project_changelist"))

        self.assertEqual(response.status_code, 200)

    def test_languages_are_not_offered_in_the_skills_picker(self):
        """Languages live on Project.language. A language attached through the
        skills relation is read by nothing, so offering it here only invited
        selecting the same language twice, once to no effect."""
        from main.admin import ProjectAdmin
        from django.contrib import admin as django_admin

        Skill.objects.create(skill="Rust", category=Skill.Category.LANGUAGE)
        capability = Skill.objects.get(skill="Systems Integration")

        model_admin = ProjectAdmin(Project, django_admin.site)
        field = model_admin.formfield_for_manytomany(
            Project._meta.get_field("skills"), None)
        offered = list(field.queryset)

        self.assertIn(capability, offered)
        self.assertNotIn(Skill.objects.get(skill="Rust"), offered)

    def test_the_skills_picker_is_alphabetical(self):
        """Skill.Meta.ordering groups by category then sort_order, which reads
        as no order at all when scanning a list for one name."""
        from main.admin import ProjectAdmin
        from django.contrib import admin as django_admin

        model_admin = ProjectAdmin(Project, django_admin.site)
        field = model_admin.formfield_for_manytomany(
            Project._meta.get_field("skills"), None)

        names = [s.skill for s in field.queryset]

        self.assertEqual(names, sorted(names))

    def test_skill_list_renders(self):
        response = self.client.get(reverse("admin:main_skill_changelist"))

        self.assertEqual(response.status_code, 200)

    def test_capabilities_survive_a_round_trip_through_the_form(self):
        capability = Skill.objects.get(skill="Systems Integration")

        self.project.skills.add(capability)

        self.assertEqual([s.skill for s in self.project.capabilities],
                         ["Systems Integration"])


class CapabilityFilterTests(TestCase):
    """Phase 2: capability leads, language demotes, and the whole group
    disappears while no project claims one."""

    def setUp(self):
        self.integration = Skill.objects.get(skill="Systems Integration")
        self.interop = Skill.objects.get(skill="Healthcare Interoperability")
        self.platform = Skill.objects.create(
            skill="Esker", category=Skill.Category.PLATFORM)

        self.tagged = Project.objects.create(
            title="Referral Pipeline", briefDescription="b", content="c",
            language="Python")
        self.untagged = Project.objects.create(
            title="Side Project", briefDescription="b", content="c",
            language="Python")

    def _html(self):
        return self.client.get(reverse("main:portfolio")).content.decode()

    def test_capability_menu_is_absent_until_a_project_claims_one(self):
        """The empty-taxonomy state. An unfilled group points straight at the
        gap it is meant to fill."""
        html = self._html()

        self.assertNotIn("menu-capability", html)
        self.assertNotIn("data-filter-capability=\"", html.split("cardContainer")[0])

    def test_capability_menu_appears_once_a_project_claims_one(self):
        self.tagged.skills.add(self.integration)

        html = self._html()

        self.assertIn("menu-capability", html)
        self.assertIn("Systems Integration", html)

    def test_unused_capabilities_are_not_offered(self):
        """Six are seeded; only the ones in use should be selectable, or the
        menu advertises what is missing."""
        self.tagged.skills.add(self.integration)

        html = self._html()

        self.assertIn("Systems Integration", html)
        self.assertNotIn("Healthcare Interoperability", html)

    def test_cards_carry_capability_slugs_for_filtering(self):
        """Order is deterministic: Skill.Meta.ordering sorts by sort_order, and
        the seed gives Systems Integration 10 and Healthcare Interoperability
        20."""
        self.tagged.skills.add(self.integration, self.interop)

        html = self._html()

        self.assertIn(
            'data-filter-capability="systems-integration healthcare-interoperability"',
            html)

    def test_untagged_card_has_an_empty_capability_attribute(self):
        """Empty rather than missing: the attribute has to exist so an OR
        filter can exclude the card rather than error on it."""
        self.tagged.skills.add(self.integration)

        html = self._html()

        self.assertIn('data-filter-capability=""', html)

    def test_capability_is_the_first_filter_menu(self):
        """Order in the DOM is the order on screen, and the JS reads its
        category order from the DOM too."""
        self.tagged.skills.add(self.integration)

        html = self._html()

        self.assertLess(html.index("menu-capability"), html.index("menu-language"))

    def test_languages_move_below_the_description(self):
        self.tagged.skills.add(self.integration)

        html = self._html()

        self.assertIn("project-card__tech", html)
        self.assertLess(html.index("project-card__tags"), html.index("project-card__tech"))

    def test_platforms_render_as_supporting_detail_not_capabilities(self):
        self.tagged.skills.add(self.integration, self.platform)

        html = self._html()
        card = html.split("project-card__tags")[1]

        # Esker is a platform, so it belongs in the quiet tech run, not as a
        # prominent capability tag.
        self.assertLess(card.index("project-card__tech"), card.index("Esker"))

    def test_filter_list_context_includes_capability_only_when_used(self):
        from main.views import build_portfolio_context

        without = build_portfolio_context({}, [], [])
        self.assertNotIn("data-filter-capability", without)

        with_one = build_portfolio_context(
            {}, [], [{"skill": self.integration, "count": 1}])
        self.assertEqual(with_one["data-filter-capability"], "systems-integration")


class ProjectDateTests(TestCase):
    """date_range carries all the formatting, so the templates stay dumb."""

    def _range(self, start, end):
        return Project(startDate=start, endDate=end).date_range

    def test_both_dates_render_as_a_span(self):
        self.assertEqual(
            self._range(date(2024, 3, 1), date(2024, 8, 9)),
            "Mar 2024 – Aug 2024")

    def test_an_open_end_date_reads_as_ongoing(self):
        """Matches how a null Job.endDate already renders in Experience."""
        self.assertEqual(self._range(date(2024, 3, 1), None),
                         "Mar 2024 – Present")

    def test_a_single_month_is_not_repeated(self):
        self.assertEqual(self._range(date(2024, 3, 1), date(2024, 3, 28)),
                         "Mar 2024")

    def test_end_date_alone_renders_alone(self):
        self.assertEqual(self._range(None, date(2024, 8, 1)), "Aug 2024")

    def test_no_dates_renders_nothing(self):
        """Empty string, not None, so a template can test it directly."""
        self.assertEqual(self._range(None, None), "")

    def test_dates_appear_on_the_card_only_when_set(self):
        dated = Project.objects.create(
            title="Dated", briefDescription="b", content="c", language="Python",
            startDate=date(2024, 3, 1), endDate=date(2024, 8, 1))
        Project.objects.create(title="Undated", briefDescription="b",
                               content="c", language="Python")

        html = self.client.get(reverse("main:portfolio")).content.decode()

        self.assertEqual(html.count("project-card__dates"), 1)
        self.assertIn("Mar 2024", html)

        detail = self.client.get(dated.get_absolute_url()).content.decode()
        self.assertIn("Mar 2024", detail)


class SelectedWorkTests(TestCase):
    """Phase 3: featured projects lead, and the sections vanish when nothing is
    featured rather than rendering an empty heading."""

    def setUp(self):
        self.featured = Project.objects.create(
            title="Referral Pipeline", briefDescription="b", content="c",
            language="Python", featured=True)
        self.ordinary = Project.objects.create(
            title="Side Project", briefDescription="b", content="c",
            language="Mumps")

    def _html(self):
        return self.client.get(reverse("main:portfolio")).content.decode()

    def test_no_sections_when_nothing_is_featured(self):
        """The pre-Phase-3 page: one grid, no headings."""
        self.featured.featured = False
        self.featured.save()

        html = self._html()

        self.assertNotIn("work-section", html)
        self.assertNotIn("Featured work", html)

    def test_sections_appear_once_something_is_featured(self):
        html = self._html()

        self.assertIn("Featured work", html)
        self.assertIn("More projects", html)

    def test_featured_project_renders_before_the_rest(self):
        html = self._html()

        self.assertLess(html.index("Referral Pipeline"), html.index("Side Project"))

    def test_more_projects_section_is_omitted_when_everything_is_featured(self):
        self.ordinary.featured = True
        self.ordinary.save()

        html = self._html()

        self.assertIn("Featured work", html)
        self.assertNotIn("More projects", html)

    def test_card_headings_drop_a_level_under_a_section(self):
        """h1 -> h2 section -> h3 card. Flat layout uses h2 so nothing skips."""
        self.assertIn('<h3 class="card__title"', self._html())

        self.featured.featured = False
        self.featured.save()

        self.assertIn('<h2 class="card__title"', self._html())

    def test_cards_are_still_reachable_by_the_filter_script(self):
        """The script roots at #cardContainer; sections must sit inside it."""
        html = self._html()
        container = html.split('id="cardContainer"')[1].split("filter-empty")[0]

        self.assertEqual(container.count("data-filter-capability"), 2)


class ProjectOrderingTests(TestCase):

    def _titles(self):
        html = self.client.get(reverse("main:portfolio")).content.decode()
        found = [(html.index(t), t) for t in
                 Project.objects.values_list("title", flat=True)]
        return [t for _, t in sorted(found)]

    def test_newest_first_then_alphabetical(self):
        Project.objects.create(title="Older", briefDescription="b", content="c",
                               language="Python", startDate=date(2019, 1, 1))
        Project.objects.create(title="Newer", briefDescription="b", content="c",
                               language="Python", startDate=date(2024, 1, 1))

        self.assertEqual(self._titles(), ["Newer", "Older"])

    def test_undated_projects_sort_last(self):
        """An undated project should not outrank a dated one by accident, which
        is what a naive descending sort on a nullable column does."""
        Project.objects.create(title="Undated", briefDescription="b",
                               content="c", language="Python")
        Project.objects.create(title="Dated", briefDescription="b", content="c",
                               language="Python", startDate=date(2019, 1, 1))

        self.assertEqual(self._titles(), ["Dated", "Undated"])

    def test_featured_outranks_recency(self):
        Project.objects.create(title="Recent", briefDescription="b", content="c",
                               language="Python", startDate=date(2025, 1, 1))
        Project.objects.create(title="Old Favourite", briefDescription="b",
                               content="c", language="Python",
                               startDate=date(2018, 1, 1), featured=True)

        self.assertEqual(self._titles(), ["Old Favourite", "Recent"])


class SkillsAsEvidenceTests(TestCase):
    """Phase 4: the skills list becomes an index of what is on the site."""

    def setUp(self):
        self.capability = Skill.objects.get(skill="Systems Integration")
        self.python = Skill.objects.create(
            skill="Python", category=Skill.Category.LANGUAGE)
        self.practice = Skill.objects.create(
            skill="Scrum", category=Skill.Category.PRACTICE)

        self.project = Project.objects.create(
            title="Referral Pipeline", briefDescription="b", content="c",
            language="Python, SQL")
        self.project.skills.add(self.capability)

    def _groups(self):
        from main.views import build_skill_groups
        return {g["label"]: g["skills"] for g in build_skill_groups()}

    def _entry(self, label, name):
        return next(e for e in self._groups()[label] if e["skill"] == name)

    def test_skills_are_grouped_by_category(self):
        groups = self._groups()

        self.assertIn("What I do", groups)
        self.assertIn("Languages", groups)
        self.assertIn("Ways of working", groups)

    def test_empty_groups_are_omitted(self):
        """A category with no rows gets no heading. Tooling and the practices
        are seeded by migration, so this clears them first."""
        Skill.objects.filter(category=Skill.Category.TOOLING).delete()

        self.assertNotIn("Tooling", self._groups())

    def test_capability_counts_come_from_the_relation(self):
        entry = self._entry("What I do", "Systems Integration")

        self.assertEqual(entry["count"], 1)
        self.assertEqual(entry["url"], "/portfolio/?work=systems-integration")

    def test_language_counts_come_from_the_language_field(self):
        """Not from the M2M. The language filter matches Project.language, so
        counting the relation would print a number the link contradicts —
        this skill has no project relation at all and still counts 1."""
        self.assertEqual(self.python.projects.count(), 0)

        entry = self._entry("Languages", "Python")

        self.assertEqual(entry["count"], 1)
        self.assertEqual(entry["url"], "/portfolio/?lang=Python")

    def test_language_link_uses_the_filter_key_not_the_display_name(self):
        """The portfolio filters on the enum name, so "C#" has to become
        C_Sharp or the link returns nothing."""
        Skill.objects.create(skill="C#", category=Skill.Category.LANGUAGE)
        Project.objects.create(title="Tool", briefDescription="b", content="c",
                               language="C#")

        self.assertEqual(self._entry("Languages", "C#")["url"],
                         "/portfolio/?lang=C_Sharp")

    def test_a_skill_with_no_projects_gets_no_link(self):
        """It still renders — the flat list stays complete for keyword
        matching — it just has nothing to link to."""
        self.project.skills.clear()

        entry = self._entry("What I do", "Systems Integration")

        self.assertEqual(entry["count"], 0)
        self.assertEqual(entry["url"], "")

    def test_categories_without_a_filter_axis_get_no_link(self):
        """Scrum has no portfolio filter, so a link would go nowhere."""
        self.project.skills.add(self.practice)

        entry = self._entry("Ways of working", "Scrum")

        self.assertEqual(entry["count"], 1)
        self.assertEqual(entry["url"], "")

    def test_home_page_renders_the_groups(self):
        html = self.client.get(reverse("main:index")).content.decode()

        self.assertIn("What I do", html)
        self.assertIn("skill-group__title", html)
        self.assertIn("/portfolio/?work=systems-integration", html)

    def test_counts_are_announced_to_screen_readers(self):
        """The bare numeral is decorative; the sr-only text carries meaning."""
        html = self.client.get(reverse("main:index")).content.decode()

        self.assertIn("1 project", html)

    def test_no_proficiency_ratings_are_rendered(self):
        """Deliberate: star bars invite an argument with the engineer on the
        hiring panel that cannot be won."""
        html = self.client.get(reverse("main:index")).content.decode()

        for marker in ("proficiency", "rating", "skill-level", "stars"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, html.lower())

    def test_group_order_puts_capabilities_first(self):
        from main.views import build_skill_groups

        labels = [g["label"] for g in build_skill_groups()]

        self.assertEqual(labels[0], "What I do")
        self.assertLess(labels.index("Languages"), labels.index("Ways of working"))


class ProjectLanguageFormTests(TestCase):
    """Project.language is a comma-joined CharField edited as a multi-select.

    Getting the string/list translation wrong in either direction is silent:
    the form simply opens with nothing selected and the save drops whatever
    was not re-picked.
    """

    def setUp(self):
        from main.forms import ProjectForm

        self.form_class = ProjectForm
        self.project = Project.objects.create(
            title="Referral Pipeline", briefDescription="b", content="c",
            language="Python, SQL, Mumps")

    def test_stored_languages_start_selected(self):
        form = self.form_class(instance=self.project)

        self.assertEqual(form.initial["language"], ["Python", "SQL", "Mumps"])

    def test_the_rendered_select_marks_them_selected(self):
        """The regression itself: given a string, the field iterated its
        characters and matched no option at all."""
        html = str(self.form_class(instance=self.project)["language"])

        for language in ("Python", "SQL", "Mumps"):
            with self.subTest(language=language):
                self.assertIn(f'value="{language}" selected', html)

    def test_a_single_language_still_selects(self):
        self.project.language = "Python"
        self.project.save()

        form = self.form_class(instance=self.project)

        self.assertEqual(form.initial["language"], ["Python"])

    def test_saving_stores_the_joined_string_not_a_list_repr(self):
        form = self.form_class(
            data={"title": "Referral Pipeline", "slug": "referral-pipeline",
                  "briefDescription": "b", "content": "c",
                  "language": ["Python", "SQL"], "is_personal": True},
            instance=self.project)

        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()

        self.assertEqual(saved.language, "Python, SQL")
        self.assertNotIn("[", saved.language)
        self.assertNotIn("'", saved.language)

    def test_an_edit_round_trips_without_losing_languages(self):
        """Open the form, change only the title, save. Nothing about the
        languages was touched, so all three must survive."""
        opened = self.form_class(instance=self.project)
        payload = {"title": "Renamed", "slug": "referral-pipeline",
                   "briefDescription": "b", "content": "c",
                   "language": opened.initial["language"],
                   "is_personal": True}

        form = self.form_class(data=payload, instance=self.project)
        self.assertTrue(form.is_valid(), form.errors)

        self.assertEqual(form.save().language, "Python, SQL, Mumps")

    def test_the_portfolio_view_still_parses_what_the_form_saves(self):
        """views.portfolio calls ProgramLanguage(value) on each part, which
        raises on anything the enum does not know."""
        response = self.client.get(reverse("main:portfolio"))

        self.assertEqual(response.status_code, 200)


class CredentialTests(TestCase):
    """Education holds degrees and certificates. A certificate has no GPA, and
    the field used to be required, which would have forced one to be invented."""

    def setUp(self):
        self.degree = Education.objects.create(
            degree="Bachelor of Business Administration",
            school="University of Wisconsin-Madison",
            graduationDate=date(2017, 5, 1),
            GPA="3.495",
            additionalInfo="Dean's List (three semesters)")

        self.certificate = Education.objects.create(
            degree="Project Management Certificate",
            school="University of Wisconsin-Madison",
            graduationDate=date(2024, 6, 1),
            credential_type=Education.Credential.CERTIFICATE)

    def _html(self):
        return self.client.get(reverse("main:index")).content.decode()

    def test_a_certificate_needs_no_gpa(self):
        self.assertIsNone(self.certificate.GPA)

    def test_gpa_row_is_omitted_when_absent(self):
        html = self._html()

        self.assertEqual(html.count("Overall GPA"), 1)

    def test_certificates_are_badged(self):
        html = self._html()

        self.assertIn("entry__badge", html)
        self.assertIn(">Certificate<", html)

    def test_the_degree_is_not_badged(self):
        """One badge on the page, on the certificate only."""
        self.assertEqual(self._html().count("entry__badge"), 1)

    def test_wording_matches_the_credential(self):
        html = self._html()

        self.assertIn("Completed June 2024", html)
        self.assertIn("Graduated May 2017", html)

    def test_newest_credential_leads(self):
        html = self._html()

        self.assertLess(html.index("Project Management Certificate"),
                        html.index("Bachelor of Business Administration"))

    def test_an_entry_with_neither_gpa_nor_notes_renders_no_empty_list(self):
        Education.objects.all().delete()
        Education.objects.create(
            degree="Scrum Master", school="Scrum Alliance",
            graduationDate=date(2023, 1, 1),
            credential_type=Education.Credential.CERTIFICATE)

        html = self._html()

        self.assertIn("Scrum Master", html)
        self.assertNotIn("entry__points", html)


class PublishingTests(TestCase):
    """Unpublished projects stay in the admin and never reach the site."""

    def setUp(self):
        self.live = Project.objects.create(
            title="Live Project", briefDescription="b", content="c",
            language="Python")
        self.draft = Project.objects.create(
            title="Draft Project", briefDescription="b", content="c",
            language="Python", published=False)

    def test_projects_are_published_by_default(self):
        self.assertTrue(self.live.published)

    def test_a_draft_is_absent_from_the_portfolio(self):
        html = self.client.get(reverse("main:portfolio")).content.decode()

        self.assertIn("Live Project", html)
        self.assertNotIn("Draft Project", html)

    def test_a_draft_does_not_inflate_the_card_count(self):
        html = self.client.get(reverse("main:portfolio")).content.decode()

        self.assertEqual(html.count("data-filter-capability"), 1)

    def test_a_draft_does_not_contribute_to_filter_counts(self):
        capability = Skill.objects.get(skill="Systems Integration")
        self.draft.skills.add(capability)

        html = self.client.get(reverse("main:portfolio")).content.decode()

        self.assertNotIn("menu-capability", html)


class OngoingProgrammeTests(TestCase):
    """Six simultaneous "Present" entries read as though nothing finishes."""

    def test_a_programme_reads_as_ongoing(self):
        project = Project(startDate=date(2020, 8, 1), is_ongoing_program=True)

        self.assertEqual(project.date_range, "Ongoing since Aug 2020")

    def test_an_ordinary_open_project_still_reads_as_present(self):
        project = Project(startDate=date(2026, 4, 1))

        self.assertEqual(project.date_range, "Apr 2026 – Present")

    def test_the_flag_is_ignored_once_an_end_date_exists(self):
        project = Project(startDate=date(2020, 8, 1), endDate=date(2021, 2, 1),
                          is_ongoing_program=True)

        self.assertEqual(project.date_range, "Aug 2020 – Feb 2021")


class OutcomeTests(TestCase):
    """The outcome renders only once there is one, so it can be filled in later
    without leaving an empty block on the page."""

    def setUp(self):
        self.project = Project.objects.create(
            title="Referral Pipeline", briefDescription="b", content="c",
            language="Python")

    def test_blank_by_default(self):
        self.assertEqual(self.project.outcome, "")

    def test_nothing_renders_while_blank(self):
        card = self.client.get(reverse("main:portfolio")).content.decode()
        detail = self.client.get(self.project.get_absolute_url()).content.decode()

        self.assertNotIn("project-card__outcome", card)
        self.assertNotIn("outcome__label", detail)

    def test_it_renders_on_both_the_card_and_the_detail_page(self):
        self.project.outcome = "Cut manual handling by 40 hours a month."
        self.project.save()

        card = self.client.get(reverse("main:portfolio")).content.decode()
        detail = self.client.get(self.project.get_absolute_url()).content.decode()

        self.assertIn("project-card__outcome", card)
        self.assertIn("40 hours a month", card)
        self.assertIn("outcome__label", detail)
        self.assertIn("40 hours a month", detail)


class UnspecifiedLanguageTests(TestCase):
    """Unspecified is the model default, not a language."""

    def setUp(self):
        self.project = Project.objects.create(
            title="Process Design", briefDescription="b", content="c",
            language="Unspecified")

    def _tech_run(self):
        html = self.client.get(reverse("main:portfolio")).content.decode()
        return html.split("project-card__tech")[1].split("</ul>")[0]

    def test_it_is_not_listed_on_the_card(self):
        """The data-filter-lang attribute still carries the raw value, which is
        correct; what must not appear is the visible tech run."""
        self.assertNotIn("Unspecified", self._tech_run())

    def test_it_is_not_offered_as_a_filter(self):
        html = self.client.get(reverse("main:portfolio")).content.decode()

        self.assertNotIn('data-filter-label="Unspecified"', html)

    def test_the_detail_page_omits_the_language_row(self):
        html = self.client.get(self.project.get_absolute_url()).content.decode()

        self.assertNotIn("Unspecified", html)
        self.assertNotIn("<dt>Language</dt>", html)

    def test_real_languages_are_still_listed(self):
        self.project.language = "Python, Unspecified"
        self.project.save()

        run = self._tech_run()

        self.assertIn("Python", run)
        self.assertNotIn("Unspecified", run)


class FilterCountTests(TestCase):
    """Counts come from the same pass that builds the cards, so what a filter
    promises and what it returns cannot disagree."""

    def setUp(self):
        self.capability = Skill.objects.get(skill="Systems Integration")

        for i in range(3):
            project = Project.objects.create(
                title=f"Integration {i}", briefDescription="b", content="c",
                language="Python", is_personal=False)
            project.skills.add(self.capability)

        Project.objects.create(title="Hobby", briefDescription="b", content="c",
                               language="Python", is_personal=True)

    def test_capability_count_matches_the_projects(self):
        html = self.client.get(reverse("main:portfolio")).content.decode()
        menu = html.split('id="menu-capability"')[1].split("</ul>")[0]

        self.assertIn('data-filter-label="Systems Integration"', menu)
        self.assertIn(">3</span>", menu)

    def test_kind_counts_are_rendered(self):
        html = self.client.get(reverse("main:portfolio")).content.decode()
        menu = html.split('id="menu-kind"')[1].split("</ul>")[0]

        self.assertIn('data-filter-label="Personal"', menu)
        self.assertIn('data-filter-label="Professional"', menu)

    def test_languages_with_no_projects_are_not_offered(self):
        """Every ProgramLanguage choice used to be listed whether a project used
        it or not, so most of the menu returned nothing."""
        html = self.client.get(reverse("main:portfolio")).content.decode()
        menu = html.split('id="menu-language"')[1].split("</ul>")[0]

        self.assertIn('data-filter-label="Python"', menu)
        self.assertNotIn('data-filter-label="PHP"', menu)

    def test_the_plain_label_is_exposed_for_the_chips(self):
        """The button text now also holds a count, and a chip reading
        "Systems Integration 3" would be wrong."""
        html = self.client.get(reverse("main:portfolio")).content.decode()

        self.assertIn('data-filter-label="Systems Integration"', html)


class SkillMergeActionTests(TestCase):
    """Taxonomy changes without a migration each time."""

    def setUp(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("editor", "e@example.com", "pw")
        self.client.force_login(User.objects.get(username="editor"))

        self.keep = Skill.objects.create(skill="Copilot",
                                         category=Skill.Category.TOOLING)
        self.drop = Skill.objects.create(skill="Copilot X",
                                         category=Skill.Category.TOOLING)

        self.project = Project.objects.create(
            title="Assisted Build", briefDescription="b", content="c",
            language="Python")
        self.project.skills.add(self.drop)

    def _post(self, **extra):
        data = {"action": "merge_skills",
                "_selected_action": [self.keep.pk, self.drop.pk]}
        data.update(extra)
        return self.client.post(reverse("admin:main_skill_changelist"), data)

    def test_it_asks_before_merging(self):
        response = self._post()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Merge skills")
        self.assertTrue(Skill.objects.filter(pk=self.drop.pk).exists())

    def test_confirming_retags_and_deletes(self):
        self._post(merge_confirmed="1", target=self.keep.pk)

        self.assertFalse(Skill.objects.filter(pk=self.drop.pk).exists())
        self.assertEqual([s.skill for s in self.project.skills.all()],
                         ["Copilot"])

    def test_the_target_survives(self):
        self._post(merge_confirmed="1", target=self.keep.pk)

        self.assertTrue(Skill.objects.filter(pk=self.keep.pk).exists())


class TaxonomyRefreshTests(TestCase):
    """Migration 0011 sharpened the capability axis."""

    def test_the_ai_capability_exists(self):
        skill = Skill.objects.get(skill="AI & LLM Solutions")

        self.assertEqual(skill.category, Skill.Category.CAPABILITY)
        self.assertEqual(skill.slug, "ai-and-llm-solutions")

    def test_web_applications_was_renamed(self):
        self.assertFalse(Skill.objects.filter(skill="Web Applications").exists())
        self.assertTrue(
            Skill.objects.filter(skill="SaaS Platform Development").exists())

    def test_the_generic_ai_tag_is_gone_but_llm_remains(self):
        self.assertFalse(Skill.objects.filter(skill__iexact="AI").exists())
        self.assertTrue(Skill.objects.filter(skill="LLM").exists())

    def test_claude_is_now_the_named_tool(self):
        self.assertFalse(Skill.objects.filter(skill__iexact="Claude").exists())
        self.assertTrue(Skill.objects.filter(skill="Claude Code").exists())


class EvidenceCountTests(TestCase):
    """The admin's Projects column, and the warning it shows at zero.

    Languages are stored in Project.language rather than the skills relation,
    so counting them through `Skill.projects` reported zero for every language
    while the warning was suppressed for exactly those rows -- leaving one
    arbitrary-looking flag on the page and JavaScript reading 0 with ten
    projects behind it.
    """

    def setUp(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("editor", "e@example.com", "pw")
        self.client.force_login(User.objects.get(username="editor"))

        self.javascript = Skill.objects.create(
            skill="JavaScript", category=Skill.Category.LANGUAGE)
        self.rust = Skill.objects.create(
            skill="Rust", category=Skill.Category.LANGUAGE)
        self.capability = Skill.objects.get(skill="Systems Integration")
        self.unused = Skill.objects.create(
            skill="Kubernetes", category=Skill.Category.PLATFORM)

        for i in range(3):
            project = Project.objects.create(
                title=f"Integration {i}", briefDescription="b", content="c",
                language="JavaScript, TypeScript")
            project.skills.add(self.capability)

    def _count(self, skill):
        from django.db.models import Count, Q

        from main.admin import render_evidence_count
        from main.models import language_project_counts

        row = (Skill.objects
               .annotate(tagged_count=Count(
                   "projects", filter=Q(projects__published=True)))
               .get(pk=skill.pk))

        return render_evidence_count(row, language_project_counts(),
                                     row.tagged_count)

    def test_a_language_is_counted_from_the_language_field(self):
        self.assertEqual(self._count(self.javascript), 3)

    def test_a_capability_is_counted_from_the_relation(self):
        self.assertEqual(self._count(self.capability), 3)

    def test_an_unused_language_warns_like_any_other_skill(self):
        """Previously exempted, which is why the flag looked arbitrary."""
        self.assertIn("&#9888;", str(self._count(self.rust)))

    def test_an_unused_non_language_warns(self):
        self.assertIn("&#9888;", str(self._count(self.unused)))

    def test_partial_names_do_not_match(self):
        """"Java" must not be credited with JavaScript's projects."""
        java = Skill.objects.create(skill="Java",
                                    category=Skill.Category.LANGUAGE)

        self.assertIn("&#9888;", str(self._count(java)))

    def test_unpublished_projects_are_not_evidence(self):
        draft = Project.objects.create(
            title="Draft", briefDescription="b", content="c",
            language="Rust", published=False)
        draft.skills.add(self.unused)

        self.assertIn("&#9888;", str(self._count(self.rust)))
        self.assertIn("&#9888;", str(self._count(self.unused)))

    def test_unspecified_is_never_counted(self):
        Project.objects.create(title="Process", briefDescription="b",
                               content="c", language="Unspecified")
        unspecified = Skill.objects.create(
            skill="Unspecified", category=Skill.Category.LANGUAGE)

        self.assertIn("&#9888;", str(self._count(unspecified)))

    def test_the_changelist_renders(self):
        response = self.client.get(reverse("admin:main_skill_changelist"))

        self.assertEqual(response.status_code, 200)

    def test_the_home_page_agrees_with_the_admin(self):
        """Both read the same helper, so the number a recruiter sees and the
        number in the admin cannot drift apart."""
        from main.views import build_skill_groups

        groups = {g["label"]: g["skills"] for g in build_skill_groups()}
        entry = next(e for e in groups["Languages"] if e["skill"] == "JavaScript")

        self.assertEqual(entry["count"], self._count(self.javascript))


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


class JobResponsibilityTests(TestCase):
    """Bullets are lines of text on the job itself.

    They were rows in a JobDetail table with no ordering declared and no
    ORDER BY in the query, so the page rendered them in whatever order SQLite
    returned and a bullet could not be moved. A line in a textarea can.
    """

    def _job(self, responsibilities):
        return Job.objects.create(
            employer="Esker Inc", title="Solution Architect",
            startDate=date(2025, 4, 1), responsibilities=responsibilities)

    def test_lines_come_back_in_the_order_they_were_typed(self):
        job = self._job("Lead the team\nShip the thing\nWrite it down")

        self.assertEqual(job.responsibility_lines,
                         ["Lead the team", "Ship the thing", "Write it down"])

    def test_reordering_the_text_reorders_the_bullets(self):
        """The whole point of the change."""
        job = self._job("Second\nFirst")
        job.responsibilities = "First\nSecond"

        self.assertEqual(job.responsibility_lines, ["First", "Second"])

    def test_blank_lines_are_dropped(self):
        job = self._job("One\n\n\nTwo\n")

        self.assertEqual(job.responsibility_lines, ["One", "Two"])

    def test_carriage_returns_do_not_survive(self):
        """A browser submits a textarea with CRLF endings, and a lone CR is
        possible from a paste. strip() covers the first -- splitlines() is what
        covers the second, which would otherwise join two bullets into one with
        a control character wedged between them."""
        crlf = self._job("One\r\nTwo\r\nThree")
        lone_cr = self._job("Four\rFive")

        self.assertEqual(crlf.responsibility_lines, ["One", "Two", "Three"])
        self.assertEqual(lone_cr.responsibility_lines, ["Four", "Five"])

    def test_surrounding_whitespace_is_trimmed(self):
        job = self._job("  Indented  \n\tTabbed")

        self.assertEqual(job.responsibility_lines, ["Indented", "Tabbed"])

    def test_a_job_with_no_bullets_has_none(self):
        self.assertEqual(self._job("").responsibility_lines, [])

    def test_the_page_renders_them_in_order(self):
        self._job("Alpha bullet\nBeta bullet\nGamma bullet")

        html = self.client.get(reverse("main:index")).content.decode()
        points = html.split('class="entry__points"')[1].split("</ul>")[0]

        self.assertEqual(re.findall(r"<li>([^<]+)</li>", points),
                         ["Alpha bullet", "Beta bullet", "Gamma bullet"])

    def test_no_empty_list_renders_for_a_job_without_bullets(self):
        """An empty <ul> is invalid markup and would still draw the list's
        spacing."""
        self._job("")

        html = self.client.get(reverse("main:index")).content.decode()

        self.assertNotIn('class="entry__points"', html)


class JobBackfillMigrationTests(TestCase):
    """Migration 0012 moves the JobDetail rows onto the job.

    The functions take the historical model registry, and read nothing from it
    but get_model, so the live registry drives them just as well.
    """

    @staticmethod
    def _migration():
        from importlib import import_module

        return import_module("main.migrations.0012_job_responsibilities")

    def setUp(self):
        from django.apps import apps

        from .models import JobDetail

        self.apps = apps
        self.JobDetail = JobDetail
        self.job = Job.objects.create(
            employer="Esker Inc", title="Solution Architect",
            startDate=date(2025, 4, 1))

    def _detail(self, content):
        return self.JobDetail.objects.create(relatedJob=self.job,
                                             content=content)

    def test_rows_are_joined_in_primary_key_order(self):
        """Primary key order is the order the page was already rendering, so
        the backfill freezes what was on the site rather than changing it."""
        for content in ("First", "Second", "Third"):
            self._detail(content)

        self._migration().forwards(self.apps, None)
        self.job.refresh_from_db()

        self.assertEqual(self.job.responsibility_lines,
                         ["First", "Second", "Third"])

    def test_empty_rows_are_not_carried_over(self):
        self._detail("Real")
        self._detail("   ")

        self._migration().forwards(self.apps, None)
        self.job.refresh_from_db()

        self.assertEqual(self.job.responsibility_lines, ["Real"])

    def test_a_re_run_does_not_overwrite_text_edited_since(self):
        """The JobDetail rows stay in place for a release, so they are still
        readable -- and still stale -- after the wording has been reworked in
        the admin. A rollback and re-apply must not put the old wording back.
        """
        self._detail("Original wording")
        migration = self._migration()
        migration.forwards(self.apps, None)

        self.job.responsibilities = "Reworked wording"
        self.job.save(update_fields=["responsibilities"])

        migration.forwards(self.apps, None)
        self.job.refresh_from_db()

        self.assertEqual(self.job.responsibility_lines, ["Reworked wording"])

    def test_a_job_with_no_rows_is_left_alone(self):
        self._migration().forwards(self.apps, None)
        self.job.refresh_from_db()

        self.assertEqual(self.job.responsibilities, "")

    def test_it_reverses(self):
        for content in ("First", "Second"):
            self._detail(content)

        migration = self._migration()
        migration.forwards(self.apps, None)
        migration.backwards(self.apps, None)
        self.job.refresh_from_db()

        self.assertEqual(self.job.responsibilities, "")
        self.assertEqual(
            [d.content for d in self.JobDetail.objects.filter(relatedJob=self.job)],
            ["First", "Second"])

    def test_reversing_does_not_double_the_rows(self):
        """The rows the forward pass read are still there, so rebuilding
        without clearing first would leave two of each."""
        self._detail("First")

        migration = self._migration()
        migration.forwards(self.apps, None)
        migration.backwards(self.apps, None)

        self.assertEqual(
            self.JobDetail.objects.filter(relatedJob=self.job).count(), 1)


class WorkSectionGroupingTests(TestCase):
    """The featured group is drawn as a panel and the rest is introduced by a
    labelled rule, so a short final row reads as padding inside a container
    rather than as cards that failed to load.

    Both treatments hang off a modifier class, so the class is the contract.
    """

    def setUp(self):
        Project.objects.create(
            title="Referral Pipeline", briefDescription="b", content="c",
            language="Python", featured=True)
        Project.objects.create(
            title="Side Project", briefDescription="b", content="c",
            language="Mumps")

    def _html(self):
        return self.client.get(reverse("main:portfolio")).content.decode()

    def test_the_featured_group_is_a_panel(self):
        self.assertIn("work-section--featured", self._html())

    def test_the_rest_is_introduced_by_the_rule(self):
        self.assertIn("work-section--more", self._html())

    def test_neither_modifier_survives_when_nothing_is_featured(self):
        """With no featured work the page is one unlabelled grid, so a panel
        around nothing would be a box with a heading and no contents."""
        Project.objects.update(featured=False)

        html = self._html()

        self.assertNotIn("work-section--featured", html)
        self.assertNotIn("work-section--more", html)


class DarkPaletteTests(TestCase):
    """app.css declares the dark palette twice -- once for the OS preference
    and once for an explicit choice -- and says the two must be kept identical.

    A token added to one and not the other is invisible until someone toggles
    the theme, which is exactly the kind of thing nobody checks.
    """

    @staticmethod
    def _tokens(css, opener):
        start = css.index(opener) + len(opener)
        body = css[start:css.index("}", start)]

        return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", body))

    def setUp(self):
        from django.conf import settings

        path = (Path(settings.BASE_DIR) / "main" / "static" / "main" / "css"
                / "app.css")
        self.css = path.read_text(encoding="utf-8")

    def test_the_two_dark_blocks_declare_the_same_tokens(self):
        from_media = self._tokens(self.css, ':root:not([data-theme="light"]) {')
        from_attribute = self._tokens(self.css, ':root[data-theme="dark"] {')

        self.assertEqual(from_media, from_attribute)

    def test_every_dark_token_has_a_light_default(self):
        """A token that only exists in the dark blocks resolves to nothing in
        light mode, and the property silently falls back to its initial value."""
        light = self._tokens(self.css, ":root {")
        dark = self._tokens(self.css, ':root[data-theme="dark"] {')

        self.assertEqual(sorted(set(dark) - set(light)), [])


class ManualOrderTests(TestCase):
    """sort_order pins a project to the top of its own section.

    The default is newest first, which is right until it isn't -- the project
    worth leading with is not always the most recent one. A number overrides
    that, and a blank leaves it alone.
    """

    def setUp(self):
        self.old = Project.objects.create(
            title="Oldest", briefDescription="b", content="c",
            language="Python", startDate=date(2019, 1, 1))
        self.middle = Project.objects.create(
            title="Middle", briefDescription="b", content="c",
            language="Python", startDate=date(2022, 1, 1))
        self.new = Project.objects.create(
            title="Newest", briefDescription="b", content="c",
            language="Python", startDate=date(2025, 1, 1))

    def _section(self, name="other_projects"):
        response = self.client.get(reverse("main:portfolio"))
        return [project.title for project, _ in response.context[name]]

    def test_the_default_is_newest_first(self):
        self.assertEqual(self._section(), ["Newest", "Middle", "Oldest"])

    def test_a_numbered_project_leads_its_section(self):
        self.old.sort_order = 1
        self.old.save()

        self.assertEqual(self._section(), ["Oldest", "Newest", "Middle"])

    def test_numbers_order_among_themselves(self):
        for project, number in ((self.new, 3), (self.old, 1), (self.middle, 2)):
            project.sort_order = number
            project.save()

        self.assertEqual(self._section(), ["Oldest", "Middle", "Newest"])

    def test_every_numbered_project_outranks_every_blank_one(self):
        """Including when the blank one is newer, which is the whole point."""
        self.old.sort_order = 99
        self.old.save()

        self.assertEqual(self._section()[0], "Oldest")

    def test_projects_sharing_a_number_fall_back_to_the_default(self):
        self.old.sort_order = 1
        self.old.save()
        self.new.sort_order = 1
        self.new.save()

        self.assertEqual(self._section(), ["Newest", "Oldest", "Middle"])

    def test_zero_is_a_real_rank_and_not_a_blank(self):
        """Nullable rather than defaulted precisely so these differ."""
        self.old.sort_order = 0
        self.old.save()

        self.assertEqual(self._section()[0], "Oldest")


class ManualOrderSectionTests(TestCase):
    """The override reorders within a section; it never moves between them."""

    def setUp(self):
        self.featured_old = Project.objects.create(
            title="Featured Old", briefDescription="b", content="c",
            language="Python", startDate=date(2019, 1, 1), featured=True)
        self.featured_new = Project.objects.create(
            title="Featured New", briefDescription="b", content="c",
            language="Python", startDate=date(2025, 1, 1), featured=True)
        self.other = Project.objects.create(
            title="Ordinary", briefDescription="b", content="c",
            language="Python", startDate=date(2026, 1, 1))

    def _sections(self):
        response = self.client.get(reverse("main:portfolio"))
        return ([p.title for p, _ in response.context["featured_projects"]],
                [p.title for p, _ in response.context["other_projects"]])

    def test_a_number_reorders_inside_the_featured_section(self):
        self.featured_old.sort_order = 1
        self.featured_old.save()

        featured, _ = self._sections()

        self.assertEqual(featured, ["Featured Old", "Featured New"])

    def test_a_numbered_ordinary_project_does_not_join_the_featured_section(self):
        """A low number on an unfeatured project must not promote it past the
        featured work -- featured is the outer sort and stays that way."""
        self.other.sort_order = 1
        self.other.save()

        featured, other = self._sections()

        self.assertEqual(featured, ["Featured New", "Featured Old"])
        self.assertEqual(other, ["Ordinary"])

    def test_the_card_order_on_the_page_matches_the_context(self):
        """The template walks the two lists in turn, so what the view decided
        is what a visitor sees."""
        self.featured_old.sort_order = 1
        self.featured_old.save()

        html = self.client.get(reverse("main:portfolio")).content.decode()
        positions = [html.index(f">{title}</h3>")
                     for title in ("Featured Old", "Featured New", "Ordinary")]

        self.assertEqual(positions, sorted(positions))


class EagerImageTests(TestCase):
    """The three images loaded eagerly have to be the three shown first.

    `lazy` is decided by position in the ordered queryset, while the page is
    drawn from the featured/other split of that same queryset. If the two ever
    disagree -- say a manually ordered unfeatured project took an eager slot --
    a card above the fold would be told to load lazily and a card further down
    would load eagerly instead.
    """

    def setUp(self):
        # Three featured, so all three eager slots belong to the featured
        # section. With two, a slot stolen by an unfeatured project lands in
        # the same position either way and the bug hides.
        for n in range(3):
            Project.objects.create(
                title=f"Featured {n}", briefDescription="b", content="c",
                language="Python", startDate=date(2020 + n, 1, 1), featured=True)

        for n in range(3):
            Project.objects.create(
                title=f"Ordinary {n}", briefDescription="b", content="c",
                language="Python", startDate=date(2023 + n, 1, 1))

    def _eager_flags(self):
        """True where the card's image loads eagerly, in render order."""
        html = self.client.get(reverse("main:portfolio")).content.decode()
        body = html.split('id="cardContainer"')[1]

        return ['loading="lazy"' not in tag
                for tag in re.findall(r"<img [^>]*>", body)]

    def test_exactly_the_first_three_cards_load_eagerly(self):
        self.assertEqual(self._eager_flags(),
                         [True, True, True, False, False, False])

    def test_a_manual_order_does_not_steal_an_eager_slot(self):
        """Numbering an unfeatured project moves it up its own section, not
        into the run of cards that load first."""
        ordinary = Project.objects.get(title="Ordinary 0")
        ordinary.sort_order = 1
        ordinary.save()

        self.assertEqual(self._eager_flags(),
                         [True, True, True, False, False, False])
