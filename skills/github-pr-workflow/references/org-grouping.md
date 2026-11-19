# Grouping Repositories Across an Organization

GitHub has no folders or nested grouping. Only two things group repos, and they do different jobs:

| Mechanism | What it gives | Scope needed |
|---|---|---|
| **Topics** | Tags on the repo page, visible to everyone, searchable (`org:X topic:calc`) | `repo` |
| **Custom properties** | Org-level metadata with an enforced value list, drives the `prop` filter on the org Repositories page and can target rulesets | `admin:org` (classic) / `organization_custom_properties:write` (fine-grained) |

No topic filter exists in the org Repositories list — that filter only comes from custom properties. Set topics anyway: they are free, visible on the repo page, and searchable globally.

**Topics (replaces the whole list, does not append):**

```bash
gh api --method PUT "repos/$ORG/$REPO/topics" -H "Accept: application/vnd.github+json" -f "names[]=calculators"
```

**Custom property definition** — `PUT /orgs/{org}/properties/schema/{custom_property_name}`. The property name is a **path segment**, not a body field:

```bash
gh api --method PUT "/orgs/$ORG/properties/schema/product" -H "Accept: application/vnd.github+json" \
  --input - <<'JSON'
{"value_type":"single_select","allowed_values":["calculators","content"],"values_editable_by":"org_actors","required":false,"description":"Repository group"}
JSON
```

**Custom property values** — `PATCH /orgs/{org}/properties/values`; `properties` is an array of `{property_name, value}` objects, `repository_names` caps at 30 per call:

```bash
gh api --method PATCH "/orgs/$ORG/properties/values" -H "Accept: application/vnd.github+json" \
  --input - <<'JSON'
{"repository_names":["repo-a","repo-b"],"properties":[{"property_name":"product","value":"calculators"}]}
JSON
```

Verification: `GET /orgs/{org}/properties/schema` (empty `[]` means the feature is available but nothing is defined) and `GET /orgs/{org}/properties/values` (per-repo values). Check topics back with `GET /repos/{o}/{r}/topics`.

Pitfalls:

- `PUT /orgs/{org}/properties/schema` (collection form with a `properties` array) does not exist and 404s. One property = one call with the name in the path.
- A 404 from the custom-properties endpoints is usually a **scope** problem, not a missing org: the error text says `needs the "admin:org" scope`. Check `gh auth status` scopes first, and if `admin:org` is absent, hand the user the UI path (Org → Settings → Code, planning, and automation → Repository → Custom properties → New property, then the **Set values** tab) rather than guessing at a workaround.
- Custom properties are available on the Free plan (docs frontmatter `versions: fpt: '*'`); the schema endpoint answering with `[]` on a free org confirms the feature, not a plan limitation.
- Custom properties and topics never touch the repo path: URLs and existing clones keep working. Only renaming changes the path, and GitHub leaves a redirect from the old name.
- Topic names must be lowercase alphanumeric plus hyphen; a topic whose name collides with a language (`python`) makes the repo read as that language in filters.

When an endpoint you assume 404s, read the real path out of GitHub's OpenAPI description instead of guessing again:

```bash
WORKDIR=<workdir>   # task working directory, outside the repo
cd "$WORKDIR"
curl -sL https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json -o ghapi.json
python3 -c "import json;d=json.load(open('ghapi.json'));[print(p, list(d['paths'][p])) for p in d['paths'] if 'propert' in p]"
```

## Creating a repository in someone else's org

- Creating a repository in the owner's org and pushing the first commit is the owner's action, not a routine step: do it only when the request names the repo in the same turn. A "yes" picked from a choice list is not durable permission.
- Know your undo before pushing: `gh repo delete` needs the `delete_repo` scope and otherwise answers `HTTP 403 ... needs the "delete_repo" scope`. `gh auth refresh -h github.com -s delete_repo` is interactive, so it cannot be done silently mid-task; without it, deletion is UI-only — say that plainly instead of promising a rollback you cannot perform.
- Org policy can forbid deploy keys: `gh repo deploy-key add` answers `422 Deploy keys are disabled for this repository`. Read-only is the default (there is no `--allow-read-only` flag, only `-w/--allow-write`); if keys are blocked, plan delivery another way.
