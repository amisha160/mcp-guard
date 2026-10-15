src = open('dashboard.py', encoding='utf-8').read()
checks = [
    ('height=1, scrolling=False', 'height=1 iframe (not height=0)'),
    ('_BG_DATA_URI', 'data URI variable defined'),
    ('--mcpg-bg-img', 'CSS custom property'),
    ('background-image: var(--mcpg-bg-img', 'background-image using variable'),
    ('background-size: cover', 'cover scaling'),
    ('background-attachment: fixed', 'fixed attachment'),
    ('rgba(6,10,20,0.62)', 'readability overlay'),
    ('mcpg-bg-canvas', 'canvas element ID'),
    ('parentDoc.body.appendChild', 'canvas injected into parent DOM'),
    ('requestAnimationFrame', 'animation loop'),
    ('spawn(Math.floor', 'particle spawning'),
]
print('Dashboard implementation checks:')
all_ok = True
for code, label in checks:
    found = code in src
    status = 'OK     ' if found else 'MISSING'
    print(f'  {status}: {label}')
    if not found:
        all_ok = False
print()
print('All checks passed!' if all_ok else 'SOME CHECKS FAILED')
