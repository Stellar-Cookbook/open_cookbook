# open_cookbook  
Open Cookbook stores instances of different code snippets for writing Smart Contracts, and their subsequent call from the Frontend, and aims to facilitate the integration of newer developers into the Stellar Ecosystem by providing them access to curated Soroban synatax examples and other working code.  

## all hands on deck  
Open Cookbook is open to all members and volunteers on Stellar. Everyone is invited to share their valuable experience in the form of working stellar code, so as to help new entrants into the ecosystem receive adequate guidance and resources for reference, as they set out to write their first code in the Ecosystem.  

## recommended format  
1. fork this repository  
2. add your entry to the end of the `instances` array in `cookbook.json`  
3. the following format will be accepted: `{"title": "...", "link": "...", "why": "one sentence on why this is a good example", "network": "...", "submitted_on": "YYYY-MM-DD", "verified_by_org": "leave blank for submission"}`  
4. `network` is one of `mainnet`, `testnet`, `futurenet` or `agnostic` — use `agnostic` when the code contains no network-specific addresses or config  
5. links must be pinned to a commit SHA, not a branch name (open the file on GitHub, press `y`, then copy the URL), and should anchor the exact line or range — `#L12` or `#L12-L20`

