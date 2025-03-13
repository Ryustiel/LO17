To rename a branch in Git, you can use the following commands:

1. Rename the current branch:
   ```bash
   git branch -m new-branch-name
   ```

2. Rename a different branch:
   ```bash
   git branch -m old-branch-name new-branch-name
   ```

3. Push the renamed branch to the remote repository:
   ```bash
   git push origin new-branch-name
   ```

4. Delete the old branch from the remote repository:
   ```bash
   git push origin --delete old-branch-name
   ```

5. Reset the upstream branch for the new branch:
   ```bash
   git push --set-upstream origin new-branch-name
   ```