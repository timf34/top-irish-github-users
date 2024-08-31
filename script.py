import requests
import time
import os
import math

from config import GITHUB_TOKEN

# Use an environment variable for the token
token = GITHUB_TOKEN

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}


def fetch_users(city, page=1, per_page=100):
    url = f"https://api.github.com/search/users?q=location:{city}&sort=followers&order=desc&per_page={per_page}&page={page}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_user_details(username):
    query = """
    query($username: String!) {
      user(login: $username) {
        login
        name
        avatarUrl
        url
        repositories(first: 100, orderBy: {field: STARGAZERS, direction: DESC}) {
          totalCount
          nodes {
            name
            url
            stargazerCount
          }
        }
      }
    }
    """
    variables = {"username": username}
    response = requests.post('https://api.github.com/graphql',
                             json={'query': query, 'variables': variables},
                             headers={"Authorization": f"Bearer {token}"})
    response.raise_for_status()
    return response.json()['data']['user']


def get_all_users(city, max_users=500):
    all_users = []
    page = 1
    per_page = 100
    total_count = 0

    while len(all_users) < max_users:
        data = fetch_users(city, page, per_page)
        users = data['items']
        all_users.extend(users)
        total_count = data['total_count']

        if len(users) < per_page or len(all_users) >= total_count:
            break

        page += 1

    return all_users[:max_users]


def process_users(users):
    processed_users = []
    for user in users:
        print(f"Processing user: {user['login']}")
        details = fetch_user_details(user['login'])
        if details is None:
            continue
        total_stars = sum(repo['stargazerCount'] for repo in details['repositories']['nodes'])
        top_repos = sorted(details['repositories']['nodes'], key=lambda x: x['stargazerCount'], reverse=True)[:5]
        processed_users.append({
            'login': details['login'],
            'name': details['name'] or 'No name',
            'avatar_url': details['avatarUrl'],
            'github_url': details['url'],
            'total_stars': total_stars,
            'top_repos': top_repos
        })
    return sorted(processed_users, key=lambda x: x['total_stars'], reverse=True)


def generate_markdown(users):
    markdown_content = "# Top GitHub Users in Dublin, Ireland by Total Stars\n\n"
    markdown_content += "This list is based on the total number of stars on the user's repositories.\n\n"

    for i, user in enumerate(users[:50], 1):
        markdown_content += f"## {i}. [{user['login']}]({user['github_url']})\n\n"
        markdown_content += f"![{user['login']}]({user['avatar_url']}&s=100)\n\n"
        markdown_content += f"**Name:** {user['name']}\n\n"
        markdown_content += f"**Total Stars:** {user['total_stars']}\n\n"
        markdown_content += "**Top 5 Starred Repos:**\n\n"
        for repo in user['top_repos']:
            markdown_content += f"- [{repo['name']}]({repo['url']}) - {repo['stargazerCount']} stars\n"
        markdown_content += f"\n[View Profile]({user['github_url']})\n\n"
        markdown_content += "---\n\n"

    return markdown_content


def main():
    city = "Dublin Ireland"
    print(f"Fetching users from {city}...")
    users = get_all_users(city)
    print(f"Found {len(users)} users")

    print("Processing user data...")
    processed_users = process_users(users)

    print("Generating markdown...")
    markdown_content = generate_markdown(processed_users)

    with open("top_github_users_dublin.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print("Markdown file 'top_github_users_dublin.md' has been generated.")


if __name__ == "__main__":
    main()