# Deploying the demo

The app runs as one Fargate task behind an ECS Express Mode gateway in the
Flexion sandbox account (`991085100884`, `us-east-2`). Mai Yer created the
service on 2026-10-13; anyone with AdministratorAccess in that account can
redeploy. Nothing here needs a secret: the task role talks to Bedrock.

| Thing | Name |
| --- | --- |
| URL | https://pa-3165949bedd1422ba6996b4431230887.ecs.us-east-2.on.aws/ |
| ECR repository | `991085100884.dkr.ecr.us-east-2.amazonaws.com/pathfinder` |
| ECS cluster / service | `default` / `pathfinder-demo` (Express Mode, Fargate, ARM64, 0.5 vCPU, 1 GB) |
| Task definition family | `default-pathfinder-demo` |
| Task role | `pathfinderTaskRole` (inline policies `bedrock-haiku-5-5-only` and `bedrock-titan-embed-v2`) |
| Logs | CloudWatch `/aws/ecs/default/pathfinder-demo-96bd` |
| Env on the task | `LLM_MODEL=bedrock/converse/us.anthropic.claude-haiku-5-5`, `AWS_REGION_NAME=us-east-2`, `EMBED_MODEL=bedrock/amazon.titan-embed-text-v2:0` |

Rollouts are canary (5% for 3 minutes, then 100% with a 3-minute bake) with
automatic rollback, so a deploy takes about eight minutes and a broken image
rolls itself back.

## Redeploy

Run from `01_Product_Engineering/challenge` with AWS credentials in the
environment (paste the short-lived keys from the SSO page; never write them
to a file in the repo).

```bash
export AWS_DEFAULT_REGION=us-east-2
ACCOUNT=991085100884
REPO=$ACCOUNT.dkr.ecr.us-east-2.amazonaws.com/pathfinder
TAG=ai1-$(git rev-parse --short HEAD)        # name the tag after what is in it

# 0. TC6: the wiki is third-party text the model reads on every request. Refuse to bake
#    in a page that changed since it was screened, or that the screen flagged. No model
#    calls (DATA is an absolute path). A failure means: re-run `use_case/screen_wiki.py`
#    on the new copy and have a person read the pages it names before deploying.
(cd ../.. && uv run python use_case/screen_wiki.py --check --wiki $DATA/wiki)   # stop here unless it exits 0

# 1. Build for the task's architecture (ARM64) and load it into local Docker.
#    DATA is a directory OUTSIDE the repo holding wiki/ (a copy of use_case/data/wiki)
#    and, optionally, embeddings_cache.json built with the task's EMBED_MODEL. It lands
#    at /data in the image. Leave --build-context off and AI-1 answers from the rules.
docker build --platform linux/arm64 --load --build-context data=$DATA -t pathfinder:$TAG .

# 2. Push.
aws ecr get-login-password | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.us-east-2.amazonaws.com
docker tag pathfinder:$TAG $REPO:$TAG
docker push $REPO:$TAG

# 3. Register a task definition that is the current one with the new image.
CURRENT=$(aws ecs describe-services --cluster default --services pathfinder-demo \
  --query 'services[0].deployments[0].taskDefinition' --output text)
aws ecs describe-task-definition --task-definition "$CURRENT" --query taskDefinition --output json \
| python3 -c '
import json, sys
td = json.load(sys.stdin)
for k in ("taskDefinitionArn", "revision", "status", "requiresAttributes", "compatibilities",
          "registeredAt", "registeredBy", "deregisteredAt"):
    td.pop(k, None)
td["containerDefinitions"][0]["image"] = sys.argv[1]
json.dump(td, sys.stdout)
' "$REPO:$TAG" > /tmp/td.json
NEW=$(aws ecs register-task-definition --cli-input-json file:///tmp/td.json \
  --query 'taskDefinition.taskDefinitionArn' --output text)

# 4. Roll the service onto it.
aws ecs update-service --cluster default --service pathfinder-demo --task-definition "$NEW"

# 5. Watch. SUCCESSFUL means done; ROLLBACK_* means the new image failed health checks.
aws ecs list-service-deployments --cluster default --service pathfinder-demo \
  --query 'serviceDeployments[0].[status,createdAt]' --output text
curl -s https://pa-3165949bedd1422ba6996b4431230887.ecs.us-east-2.on.aws/gradio_api/info \
| python3 -c 'import json,sys; print(list(json.load(sys.stdin)["named_endpoints"]))'
```

To change an environment variable, edit `environment` in `/tmp/td.json`
before step 3.

## History

| Date | Tag | What |
| --- | --- | --- |
| 2026-10-13 | `tc1-6c85ef7` | Week 1 build: `/chat`, `/compare_skills_to_role`. Service created by Mai Yer. |
| 2026-11-02 | `ai1-9e529db` | Week 3 build: adds `/ask_pathfinder`, `/suggest_competencies` and the AI-1 screen. Task definition revision 4 adds `EMBED_MODEL`. AI-1 answers from the keyword rules (`produced_by: "rules"`): the wiki is not in the image and the task role cannot call Titan. |
| 2026-11-16 | `ai1-ca3baf8` | Adds `POST /api/suggest` for the TrailSkills prototype and puts AI-1 on the model path (`produced_by: "model"`): the wiki and Titan embeddings of it are in the image at `/data`, and the task role gets `bedrock-titan-embed-v2`. Task definition revision 6. |

## AI-1 on the model path

Done on 2026-11-16. `suggest.py` reads the trailskills.org skills wiki at
`/data/wiki` and embeds it with Titan. Both now reach the task:

1. The wiki is built with `uv run python use_case/fetch_trailskills_levels.py`
   then `uv run python use_case/build_wiki.py` (writes `use_case/data/wiki`,
   gitignored). Copy it to a directory outside the repo and pass that as
   `--build-context data=$DATA` (Redeploy, step 1). The ECR repository is
   private; the content is American Trails', so do not push the image to a
   public registry.
2. `pathfinderTaskRole` has `bedrock:InvokeModel` on
   `arn:aws:bedrock:us-east-2::foundation-model/amazon.titan-embed-text-v2:0`
   (inline policy `bedrock-titan-embed-v2`).
3. After a redeploy, check a text request returns `produced_by: "model"` and
   the logs show no `AI-1 model path failed`.
