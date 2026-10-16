# Dapper wallet connection

This is a bundled, local Streamlit component using the official `@onflow/fcl` 1.21.11 SDK. The SDK opens Dapper's mainnet authentication service in a popup; no transaction or signature request is initiated by this component. Only an action and public Flow address are returned to Python. This selects a public dashboard view; it does not provide server-side proof of wallet ownership or authorise protected actions.

## Current deployment

Dapper login is **disabled by default** because the app owner has not registered a Dapper developer application. Remembering a manually selected wallet works immediately. Returning visitors are restored after asynchronous browser storage loads. An explicit URL wallet takes precedence on a new session; a remembered address never overrides an existing selection. Forgetting removes the saved address and FCL session without clearing unrelated browser storage or the agency's saved backups.

## Enable after Dapper onboarding

The official Flow SDK README states that a Dapper developer account is required: https://github.com/onflow/fcl-js/tree/master/packages/fcl#authentication

Follow Dapper's current onboarding at https://docs.meetdapper.com/get-started for the actual deployment origin (`https://mfl-management-app22.streamlit.app`). Dapper controls registration and approval of applications. Confirm that this application's website can authenticate through the mainnet FCL endpoint before enabling the button. Do not place a client secret in this component or commit it to Git.

Then add this non-secret setting in Streamlit's application settings (or as an environment variable) and restart the app:

```toml
DAPPER_LOGIN_ENABLED = true
```

Configured authentication service: `https://accounts.meetdapper.com/fcl/authn` via FCL's documented `POP/RPC` strategy. The title and site origin are passed as application metadata. Credentials remain in Dapper's own popup; only the public address and event are forwarded to the dashboard server. No live Dapper sign-in has been validated while registration is outstanding.

## Build

The checked-in bundle is served locally. Python/Streamlit deployment does not require Node, npm or a browser CDN.

```sh
cd dapper_component
npm ci --ignore-scripts
npm run build
```

Versions and package integrity hashes are pinned in `package-lock.json`. The SDK is Apache-2.0; see `APACHE-2.0.txt`. Bundled third-party notices are in `wallet.js.LEGAL.txt` and `THIRD_PARTY_NOTICES.txt`.
