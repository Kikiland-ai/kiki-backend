> Historical 0.2.1 setup/port notes. The user-authorized 0.2.2 extension adds prompt-design-engineering; the current package has 22 skills. Use the current manifests, registry, and runbook for acceptance.

# Platform-agnostic rollout

Scope: the uploaded BB8 plugin repository only. No application repository,
technology stack, prior project, account, memory, vault, or credentials are assumed.

## Now

1. Preserve the validated `bb8-cloud-plugin-0.2.1.zip` unchanged.
2. Have the caller or administrator register it as one fresh-session entry in
   `environment.plugins`, using the exact manifest name and description.
3. Run the runbook's generic acceptance prompts and record actual results.
4. `AGENTS.md` is now in place in the separate portable repository copy. Follow
   `PORTABLE-START.md` to use the reference adapter. For future application repos,
   merge with existing instructions only when that repo is explicitly in scope.

Completion: plugin identity 0.2.1, exactly 21 discovered skills, BB8 coordinator
routing, a direct specialist invocation, and context isolation all pass.

## Next

1. Keep the existing BB8 skill and harness as the vendor-neutral source.
2. The reference loader is implemented. Connect its prepared instructions to a
   selected IDE/CLI/chat host, or implement a native bridge for that host. Declare
   capability discovery, tool mappings, and reference-mode limitations explicitly.
3. Adopt the usage guide and run the same acceptance prompts on both hosts.
4. Test one missing-capability case and ensure fallback is honest.
   Also verify an explicitly scoped local repo edit in a capable host and a
   read-only fallback in a host without editing or command tools.
5. Add build-time validation for manifests, frontmatter, package inventory,
   internal links, excluded artifacts, and source/derived bundle separation.

Completion: both hosts use the same skill names and source guidance, preserve
scope, and produce equivalent routing and mission structure.

## Later

1. Add further adapters only where an actual host limitation warrants one.
2. Generate standalone bundles only for hosts that cannot load shared resources.
3. Version and document adapter changes separately from BB8 behavior changes.
4. Keep continuation files optional and task-scoped; leave knowledge features
   excluded unless the user explicitly changes the scope in a future request.

Publication, deployment, marketplace submission, and production rollout are not
performed by this draft. No dates or repo-specific commands are inferred.
