from load_data import DEV_SET_IDS, load_prospects
from website_scraper import fetch_html, find_info_links

if __name__ == "__main__":
    df = load_prospects()
    dev_set = df[df["scenario_id"].isin(DEV_SET_IDS)]
    for _, company in dev_set.iterrows():
        home_url = f"https://{company['company_domain']}"
        try:
            links = find_info_links(fetch_html(home_url), home_url)
            print(f"{company['company_name']}: {len(links)} pages {links}")
        except Exception as error:
            print(f"{company['company_name']}: FAILED ({error})")
