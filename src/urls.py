routes = ['/health', '/logs', '/prompts', '/stats', '/predict', '/generate']

for i in routes:
    print(f'curl http://localhost:8000{i}')