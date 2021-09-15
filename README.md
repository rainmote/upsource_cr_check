# upsource_cr_check
Code review check based on upsource.

Features:
- Elegant wrapper upsource API
- Support multi-dimension check, by branch or by commit
- Support environment variable replacement, better handle parameter transfer after containerization

# Instructions
1. checkout code
```
git clone git@github.com:rainmote/upsource_cr_check.git
```

2. modify `check.sh` for your upsource
```
export UPSOURCE_ENDPOINT="https://xxx.domain"
export UPSOURCE_USERNAME="admin"
export UPSOURCE_PASSWORD="passwd"
export UPSOURCE_PROJECT="projectA"
```

3. add `check.sh` to your pipline