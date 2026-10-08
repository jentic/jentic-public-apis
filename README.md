# Jentic Public APIs

<a href="https://www.producthunt.com/products/jentic-mini?embed=true&utm_source=badge-featured&utm_medium=badge&utm_campaign=badge-jentic-mini" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1107386&theme=light&t=1775041287603" alt="Jentic&#0032;Mini - Give&#0032;your&#0032;AI&#0032;agents&#0032;safe&#0032;access&#0032;to&#0032;10&#0044;000&#0043;&#0032;APIs | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

[![Discord](https://img.shields.io/badge/JOIN%20OUR%20DISCORD-COMMUNITY-7289DA?style=plastic&logo=discord&logoColor=white)](https://discord.gg/yrxmDZWMqB)

> **Join our community!** Connect with contributors and users on [Discord](https://discord.gg/yrxmDZWMqB) to discuss ideas, ask questions, and collaborate on the Jentic Public APIs repository.
>
> **Quick access API Index:** [0](index/apis/openapi/0) · [1](index/apis/openapi/1) · [2](index/apis/openapi/2) · [3](index/apis/openapi/3) · [4](index/apis/openapi/4) · [5](index/apis/openapi/5) · [6](index/apis/openapi/6) · [7](index/apis/openapi/7) · [8](index/apis/openapi/8) · [9](index/apis/openapi/9) · [A](index/apis/openapi/A) · [B](index/apis/openapi/B) · [C](index/apis/openapi/C) · [D](index/apis/openapi/D) · [E](index/apis/openapi/E) · [F](index/apis/openapi/F) · [G](index/apis/openapi/G) · [H](index/apis/openapi/H) · [I](index/apis/openapi/I) · [J](index/apis/openapi/J) · [K](index/apis/openapi/K) · [L](index/apis/openapi/L) · [M](index/apis/openapi/M) · [N](index/apis/openapi/N) · [O](index/apis/openapi/O) · [P](index/apis/openapi/P) · [Q](index/apis/openapi/Q) · [R](index/apis/openapi/R) · [S](index/apis/openapi/S) · [T](index/apis/openapi/T) · [U](index/apis/openapi/U) · [V](index/apis/openapi/V) · [W](index/apis/openapi/W) · [X](index/apis/openapi/X) · [Y](index/apis/openapi/Y) · [Z](index/apis/openapi/Z)

## Overview

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-3.0-40c463.svg)](CODE_OF_CONDUCT.md)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-blue)](LICENSE.md)

### The agentic knowledge layer

AI agents depend on APIs. Their capabilities are defined by the APIs they know about, and their reliability is defined by the quality of that knowledge. Documentation was previously nice-to-have, but for AI it's a *need-to-have*. The goal of this project is to collate all knowledge about all the world's APIs into a communal, detailed, comprehensive, structured documentation catalog designed for use by AI.  This allows AI to accurately generate API integration code, and it allows agents to plan and interact with APIs reliably, without intermediaries.

### Open source and open standards

This communal effort requires a stable but extensible representation format that can describe all salient aspects of APIs and associated workflows in full detail. The [OpenAPI specifications](https://www.openapis.org/) provide the de-facto standard for formal API descriptions, are widely adopted, supported by a vast ecosystem of associated tooling, and governed by the Linux Foundation. Importantly, the OpenAPI Initiative's most recent specification, [Arazzo](https://www.openapis.org/arazzo-specification), allows complex multi-API workflows to be described in a declarative format.

The Jentic API Directory is an open-source catalog of API and workflow descriptions that builds upon these open standards to contribute API and workflow knowledge to AI agents. We will coordinate with the OpenAPI community, and propose an RFC containing various extensions to capture additional knowledge that is especially relevant in the context of AI agents (for example concerning authentication, rate limiting, pricing, governance and safety). If you have suggestions to improve the directory, we welcome discussion on our Discord and PRs on this repository.

### AI-scale

Documenting all the world's API knowledge is made achievable by generative AI. Our starting point was OpenAPI documents provided by various vendors online (with special credit to the [APIs.guru](https://apis.guru/) repository). On top of this, we have generated thousands Arazzo workflows using AI. We are growing this repository using AI agents to import (and improve) existing OpenAPI documents and to generate new OpenAPI specifications where no structured documentation previously existed. Our AI agents are also discovering novel Arazzo workflows that can be performed on top of that API knowledge.  We will propose a scorecard evaluation to measure the quality of the generated documentation, allowing us to ensure that both the quantity and the quality of documentation increases as we progress.

We welcome all contributions from the community and from partners who want to accelerate this effort with their own resources and ingenuity. We will ensure that all contributions help the knowledge about each API and workflow in the repository to converge on the best canonical version.

### Repository Focus

The repository focuses on:
1. Standardized OpenAPI specifications for public APIs
2. Arazzo workflows that define composable operations across one or more APIs
3. Associated tooling, for example to help import and enrich documentation, or to convert it out into other formats (e.g., AI model provider's tool definition formats).
4. Evaluations and scorecards to measure API knowledge completeness, accuracy and AI-readiness
5. RFCs for extensions to open formats used in the repository, and any other proposals.

## Popular APIs

A sample of widely-used APIs in the directory. Each has a machine-readable OpenAPI spec in this repository and a human-readable, AI-readiness–scored page on [jentic.com/apis](https://jentic.com/apis). Browse the [full API Directory](https://jentic.com/apis) for 10,000+ more.

| API | Category | OpenAPI spec (this repo) | API page on jentic.com |
|-----|----------|--------------------------|-------------------------|
| Stripe | Payments | [spec](apis/openapi/stripe.com/stripe/2026-03-25.dahlia/openapi.json) | [jentic.com/apis/stripe.com/stripe](https://jentic.com/apis/stripe.com/stripe) |
| OpenAI | AI/ML | [spec](apis/openapi/openai.com/main/2.3.0/openapi.json) | [jentic.com/apis/openai.com/main](https://jentic.com/apis/openai.com/main) |
| Anthropic (Messages) | AI/ML | [spec](apis/openapi/anthropic.com/messages/1.0.0/openapi.json) | [jentic.com/apis/anthropic.com/messages](https://jentic.com/apis/anthropic.com/messages) |
| GitHub REST | Developer Tools | [spec](apis/openapi/api.github.com/main/1.1.4/openapi.json) | [jentic.com/apis/api.github.com/main](https://jentic.com/apis/api.github.com/main) |
| Slack Web API | Communications | [spec](apis/openapi/slack.com/main/1.7.0/openapi.json) | [jentic.com/apis/slack.com/main](https://jentic.com/apis/slack.com/main) |
| Gmail | Productivity | [spec](apis/openapi/googleapis.com/gmail/v1/openapi.json) | [jentic.com/apis/googleapis.com/gmail](https://jentic.com/apis/googleapis.com/gmail) |
| Notion | Productivity | [spec](apis/openapi/notion.com/notion-api/2026-03-11/openapi.json) | [jentic.com/apis/notion.com/notion-api](https://jentic.com/apis/notion.com/notion-api) |
| Shopify Admin | E-Commerce | [spec](apis/openapi/shopify.com/main/2025-01/openapi.json) | [jentic.com/apis/shopify.com/main](https://jentic.com/apis/shopify.com/main) |
| Plaid | Finance | [spec](apis/openapi/plaid.com/main/2020-09-14_1.631.0/openapi.json) | [jentic.com/apis/plaid.com/main](https://jentic.com/apis/plaid.com/main) |
| Discord | Communications | [spec](apis/openapi/discord.com/main/10/openapi.json) | [jentic.com/apis/discord.com/main](https://jentic.com/apis/discord.com/main) |
| Linear | Developer Tools | [spec](apis/openapi/linear.app/main/1.0/openapi.json) | [jentic.com/apis/linear.app/main](https://jentic.com/apis/linear.app/main) |

## Browse APIs by category

The directory is organized into categories. Below is a small sample from a few of them — follow the **View all** link for every API in that category on [jentic.com/apis](https://jentic.com/apis).

### Payments & Finance

| API | OpenAPI spec | jentic.com page |
|-----|--------------|-----------------|
| Stripe | [spec](apis/openapi/stripe.com/stripe/2026-03-25.dahlia/openapi.json) | [page](https://jentic.com/apis/stripe.com/stripe) |
| Plaid | [spec](apis/openapi/plaid.com/main/2020-09-14_1.631.0/openapi.json) | [page](https://jentic.com/apis/plaid.com/main) |
| Xero Accounting | [spec](apis/openapi/xero.com/xero_accounting/7.0.0/openapi.json) | [page](https://jentic.com/apis/xero.com/xero_accounting) |

➡️ View all in [Payments](https://jentic.com/apis?category=payments) and [Finance](https://jentic.com/apis?category=finance).

### AI/ML

| API | OpenAPI spec | jentic.com page |
|-----|--------------|-----------------|
| OpenAI | [spec](apis/openapi/openai.com/main/2.3.0/openapi.json) | [page](https://jentic.com/apis/openai.com/main) |
| Anthropic (Messages) | [spec](apis/openapi/anthropic.com/messages/1.0.0/openapi.json) | [page](https://jentic.com/apis/anthropic.com/messages) |

➡️ View all in [AI/ML](https://jentic.com/apis?category=ai-ml).

### Developer Tools

| API | OpenAPI spec | jentic.com page |
|-----|--------------|-----------------|
| GitHub REST | [spec](apis/openapi/api.github.com/main/1.1.4/openapi.json) | [page](https://jentic.com/apis/api.github.com/main) |
| Linear | [spec](apis/openapi/linear.app/main/1.0/openapi.json) | [page](https://jentic.com/apis/linear.app/main) |
| Cloudflare | [spec](apis/openapi/cloudflare.com/main/4.0.0/openapi.json) | [page](https://jentic.com/apis/cloudflare.com/main) |
| DigitalOcean | [spec](apis/openapi/digitalocean.com/main/2.0/openapi.json) | [page](https://jentic.com/apis/digitalocean.com/main) |

➡️ View all in [Developer Tools](https://jentic.com/apis?category=developer-tools).

### Communications

| API | OpenAPI spec | jentic.com page |
|-----|--------------|-----------------|
| Slack Web API | [spec](apis/openapi/slack.com/main/1.7.0/openapi.json) | [page](https://jentic.com/apis/slack.com/main) |
| Discord | [spec](apis/openapi/discord.com/main/10/openapi.json) | [page](https://jentic.com/apis/discord.com/main) |
| Twilio Messaging | [spec](apis/openapi/twilio.com/twilio_messaging_v1/1.0.0/openapi.json) | [page](https://jentic.com/apis/twilio.com/twilio_messaging_v1) |
| SendGrid Mail | [spec](apis/openapi/sendgrid.com/mail/1.0.0/openapi.json) | [page](https://jentic.com/apis/sendgrid.com/mail) |

➡️ View all in [Communications](https://jentic.com/apis?category=communications).

### Productivity

| API | OpenAPI spec | jentic.com page |
|-----|--------------|-----------------|
| Gmail | [spec](apis/openapi/googleapis.com/gmail/v1/openapi.json) | [page](https://jentic.com/apis/googleapis.com/gmail) |
| Google Calendar | [spec](apis/openapi/googleapis.com/calendar/v3/openapi.json) | [page](https://jentic.com/apis/googleapis.com/calendar) |
| Google Sheets | [spec](apis/openapi/googleapis.com/sheets/v4/openapi.json) | [page](https://jentic.com/apis/googleapis.com/sheets) |
| Notion | [spec](apis/openapi/notion.com/notion-api/2026-03-11/openapi.json) | [page](https://jentic.com/apis/notion.com/notion-api) |

➡️ View all in [Productivity](https://jentic.com/apis?category=productivity).

> Looking for something else? Search the complete catalog of **10,000+ APIs** at **[jentic.com/apis](https://jentic.com/apis)**, or jump into the raw specs via the [Quick access API Index](#jentic-public-apis) above.

## Project Stage

> **Note:** This project is currently in ALPHA.

## Documentation

* [**STRUCTURE.md**](STRUCTURE.md) - The standardized repository structure for the Jentic API Directory
* [**FEEDBACK-FILES.md**](FEEDBACK-FILES.md) - Documentation of feedback.json files that track API specification repairs
* [**CONTRIBUTING.md**](CONTRIBUTING.md) - Guidelines for contributing to the repository
* [**CODE_OF_CONDUCT.md**](CODE_OF_CONDUCT.md) - Community standards and expectations
* [**LICENSE.md**](LICENSE.md) - CC0 1.0 License for this repository

## Repository Structure

This repository follows a standardized directory structure for organizing API specifications and workflows.

- API specifications are organized by vendor and version
- Workflows are organized to clearly show which APIs they reference
- Multi-API workflows demonstrate how different services can be orchestrated together

For detailed information, please refer to the [structure documentation](STRUCTURE.md).

## AI-Readiness Scoring

OpenAPI documents in this repository can be scored for AI-readiness using the **Jentic API Scorecard CLI** — no signup, no API key, and no configuration needed.

### URL format

Files follow a predictable raw URL pattern:

```
https://raw.githubusercontent.com/jentic/jentic-public-apis/refs/heads/main/apis/openapi/{vendor}/{api-name}/{version}/openapi.json
```

### Running a score

Pass any spec URL directly to the CLI:

```bash
npx @jentic/api-scorecard-cli@latest score \
  https://raw.githubusercontent.com/jentic/jentic-public-apis/refs/heads/main/apis/openapi/swagger-api/petstore/1.0.27/openapi.json
```

![Jentic API Scorecard CLI](assets/jentic-scoring-cli.png)

To learn more about the API Scoring Cli and Jentic API AI-Readiness Framework, visit the [Jentic API Scorecard CLI repository](https://github.com/jentic/jentic-api-scorecard).

## Acknowledgments

The Jentic Public APIs project is built upon the foundation of open standards and community contributions. We extend our sincere gratitude to:

**The OpenAPI Initiative and Linux Foundation** - For creating, maintaining, and governing the OpenAPI Specification and Arazzo standards that form the backbone of this project. The OpenAPI Initiative's commitment to open standards, extensive ecosystem of tooling, and collaborative governance model directly enable our vision of a communal API knowledge layer. Special recognition goes to the technical steering committee and contributors who have developed these specifications to serve as the de-facto standard for API documentation, making structured, machine-readable API descriptions possible at scale.

**APIs.guru** - For providing the initial collection of OpenAPI specifications that helped bootstrap this repository. Their dedication to cataloging public APIs has been instrumental in our mission to create an open knowledge foundation for AI agents, and their pioneering work in API discovery laid important groundwork for projects like ours.

**The broader API community** - Including all the API providers, documentation authors, and open source contributors whose work makes comprehensive API knowledge possible. This project represents a continuation of the collaborative spirit that has driven API standardization and tooling development.

We are committed to contributing back to these communities through our proposed RFCs, quality improvements to existing specifications, and by demonstrating new applications of these open standards in the context of AI agents.

## Contributing

We welcome contributions from the community! Whether you're enhancing existing API specifications, creating new Arazzo workflows, or improving documentation, your contributions help build the open knowledge foundation for AI agents.

Please read our [Contributing Guidelines](CONTRIBUTING.md) for more information on how to get started.

## License

This project is licensed under the CC0 1.0 License - see the [LICENSE.md](LICENSE.md) file for details.

> **Disclaimer:** API specifications and workflows in this repository are based on publicly documented third-party APIs, with some modifications such as repairs to OpenAPI specs or creation of new specs from public API documentation. All **trademarks** and **service marks** are the property of their respective owners. This repository does **not** grant rights to use the underlying APIs.
