# The ecosystem you deploy into

Where your application would actually run, inside your actual firm.

> **Week 1 starts this file. Week 9 finishes it.**
> TC1 Step 10 asks eight questions. The full Week 9 checklist has around thirty,
> and the eight are a strict subset — so nothing here gets thrown away.

Describe patterns, not specifics. "On-prem OpenShift, images from an internal
registry, no public egress" is useful to everyone and identifies nobody. Never
put real hostnames, IPs, or architecture diagrams in this file.

---

## Week 1 — the first eight questions

<!-- Answered in TC1 Step 10. Bring these back from a real conversation. -->

**Who did you ask?** (role, not name)

The Optionality Orchestrator, a researcher and developer on the project's
original team who built early prototypes that did not go forward. Live Zoom
call on 2026-10-13 (recorded), with two of our team: we clicked
through the app while they watched, then asked questions. We did not put the
eight infrastructure questions to them. For this prototype the infrastructure
is ours to decide, so each row says where its answer comes from:

- **Confirmed (our deployment):** true of the running TC1 prototype, and
  checkable in our AWS account.
- **Team decision:** a choice our three-person course team made and owns.
- **From docs, not asked:** the client's production plan, read from the AWS
  grant draft and the technical-preferences note. Nobody has confirmed it.

Next conversation: a Flexion project manager closer to the project, who the
Orchestrator pointed us to. Planned to be booked for the week of 2026-10-19.

| # | Question | Answer |
| :---: | --- | --- |
| 1 | Where do internal apps run? (k8s, ECS, App Service, a VM someone maintains) | **Confirmed (our deployment):** the prototype runs as one container on Amazon ECS (Express Mode) in Flexion's AWS account, with a public HTTPS endpoint and a `/health` check. **From docs, not asked:** the client's planned production shape is serverless (static front end on S3 behind a CDN, Lambda behind API Gateway), where a Python container has no obvious home. |
| 2 | Which cloud? AWS, Azure, GCP, on-prem, several? | **Team decision:** AWS, in Flexion's account, so the prototype is not blocked by the client having no AWS account yet. **From docs, not asked:** the platform itself is planned on AWS under an AWS Imagine Grant; which account production uses is open. |
| 3 | Is there an internal container registry? | **Confirmed (our deployment):** Amazon ECR, in the same Flexion account, holds the image the service runs. Account and repository details are left out because this repo is public. |
| 4 | How do users log in? (Okta, Entra ID, Ping, SAML, homegrown) | **Team decision:** no login. A sign-in step would turn away the explorer this is built for. This departs from the spec, which has the gap view signed in, and from the grant's plan for Amazon Cognito. |
| 5 | Can the app reach the internet? Egress proxy? Allowlist? | **Team decision:** public access is required, so the app must be reachable from the open internet. **Confirmed (our deployment):** it is, at a public HTTPS URL; it calls Amazon Bedrock outbound, and the browser loads the Gradio client from a public CDN (`cdn.jsdelivr.net`). **From docs, not asked:** whether the client's production network allows either. |
| 6 | Where do secrets come from? (Vault, Secrets Manager, Key Vault) | **Team decision:** AWS Secrets Manager when the app needs a secret. **Confirmed (our deployment):** today it needs none; it reaches Bedrock through its ECS task role, so there is no key to store. |
| 7 | Who approves a deployment, and what review does it need? | **Team decision:** our three-person course team approves prototype deployments. We need control over this; it is not a client decision. **From docs, not asked:** the grant's planned platform steward role at the client would own production. |
| 8 | Is there an approved internal LLM endpoint already? | **Team decision:** Amazon Bedrock, with a low-cost model (Claude Haiku 5.5) until further analysis. **Confirmed (our deployment):** that is what the live app calls. The grant also names Bedrock as the platform's model provider, and `llm.py` is provider-agnostic, so a different model is a config change. |

**What surprised you?**

How hard it is to identify the real stakeholders. The person we reached shaped
the project early, but could not say what they would use the tool for, and
pointed us to a project manager closer to the work. And their view that
results this deterministic do not need an AI solution. Pathfinder already
computes the gaps and picks the trainings without a model and uses AI only to
reword them, so we now need to explore whether this project needs AI at all.

**What would you have to change about your app to deploy there?**

**For the prototype: nothing; it is deployed** (rows 1, 3, 5, 6 and 8). One
thing is still open: the page loads the Gradio client from a public CDN at
runtime, and vendoring it into the image would remove that dependency (Step 9
in the challenge README).

**For the client's production platform (from docs, not asked):** the plan is
TypeScript on Next.js with the model behind a provider port, so this Python app
would either run as a small container service beside the API (ECS, which the
plan does not have yet) or be ported into the TypeScript domain as the
`ModelProvider` adapter. If the no-login decision in row 4 holds, Cognito is not
needed for the explorer path.

---

## Week 1 — what your machine told you

<!--
  Paste the egress probe output from Session 1 here. It is evidence, and it
  frequently disagrees with what people believe about their own network.
-->

Run 2026-10-13 from `helpers.preflight.check_egress()` on a personal Mac on a
home network, not a managed firm laptop. 7/7 reachable, no TLS interception,
no proxy or CA environment variables set.

| Host | Why it matters | DNS | TLS | Issuer |
| --- | --- | :---: | :---: | --- |
| pypi.org | Python packages | ok | ok | GlobalSign |
| files.pythonhosted.org | the actual wheel downloads | ok | ok | GlobalSign |
| api.openai.com | the model API | ok | ok | Google Trust Services |
| cdn.jsdelivr.net | the CDN the Week 1 frontend uses | ok | ok | Sectigo |
| huggingface.co | open weights, Weeks 2 and 8 | ok | ok | Amazon |
| registry-1.docker.io | container images | ok | ok | Amazon |
| github.com | this repository | ok | ok | Sectigo |

**Does this match the table above?** It cannot yet: the table above describes
a planned AWS environment that does not exist, and this probe measured my own
network. The useful comparison is against a Lambda or container in the target
account, which is a Week 9 measurement. The one thing this already says: the
course app's CDN dependency works here and may not work there.

---

## Week 2 — could a local model work?

A local model only makes sense if users need model-written wording offline;
first test whether the templates suffice and verify real signal gaps, then
benchmark a small model on a phone if needed, and the app itself would also
have to run on the phone.

---

## Week 9 — the full checklist

<!--
  TC9 extends this same file. Do not start a new one: the point is that the git
  history shows one continuous piece of work from Week 1 to Week 9.
-->

<!-- Week 9 -->
