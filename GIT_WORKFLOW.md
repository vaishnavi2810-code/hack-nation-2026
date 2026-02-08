# Git Workflow Guide: Merging Two Branches into a New Branch

This guide explains how to merge two Git branches into a new branch, a common workflow when you want to combine features from different branches without affecting the original branches.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Method 1: Using Git Merge (Recommended)](#method-1-using-git-merge-recommended)
- [Method 2: Using Git Merge with Octopus Strategy](#method-2-using-git-merge-with-octopus-strategy)
- [Method 3: Using Git Rebase](#method-3-using-git-rebase)
- [Handling Merge Conflicts](#handling-merge-conflicts)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

When working with Git, you may need to merge two branches into a new branch for various reasons:

- Testing feature combinations before merging to main
- Creating a release branch with features from multiple development branches
- Consolidating work from parallel development streams

## Prerequisites

Before starting, ensure:

1. You have Git installed and configured
2. You have a clean working directory (no uncommitted changes)
3. You know the names of the two branches you want to merge
4. You have necessary permissions to create branches

## Method 1: Using Git Merge (Recommended)

This is the most straightforward and commonly used method.

### Step-by-Step Instructions

**Step 1: Ensure you have the latest changes**

```bash
# Fetch the latest changes from remote
git fetch origin

# Update your local branches (if they exist locally)
git checkout branch1
git pull origin branch1

git checkout branch2
git pull origin branch2
```

**Step 2: Create a new branch**

You can create the new branch from either branch1, branch2, or from main/master:

```bash
# Option A: Create from main branch (recommended)
git checkout main
git pull origin main
git checkout -b merged-branch

# Option B: Create from branch1
git checkout branch1
git checkout -b merged-branch

# Option C: Create from branch2
git checkout branch2
git checkout -b merged-branch
```

**Step 3: Merge the first branch**

If you created from main or one of the branches:

```bash
# If you created from main, merge branch1 first
git merge branch1

# If you created from branch1, this step is already done
```

**Step 4: Merge the second branch**

```bash
# Merge branch2 into your new branch
git merge branch2
```

**Step 5: Resolve any conflicts (if necessary)**

If there are merge conflicts, Git will pause and ask you to resolve them. See the [Handling Merge Conflicts](#handling-merge-conflicts) section below.

**Step 6: Verify the merge**

```bash
# Check the status
git status

# View the commit history
git log --oneline --graph --decorate --all

# Test your code to ensure everything works
```

**Step 7: Push the new branch to remote**

```bash
# Push the new merged branch to remote
git push origin merged-branch
```

### Example

```bash
# Example: Merging feature-login and feature-dashboard into combined-features

# Fetch latest changes
git fetch origin

# Create new branch from main
git checkout main
git pull origin main
git checkout -b combined-features

# Merge first branch
git merge feature-login

# Merge second branch
git merge feature-dashboard

# Push to remote
git push origin combined-features
```

## Method 2: Using Git Merge with Octopus Strategy

Git supports merging multiple branches in a single command using the "octopus" merge strategy. This creates a single merge commit with multiple parents.

### Step-by-Step Instructions

**Step 1: Create a new branch from a base (usually main)**

```bash
git checkout main
git pull origin main
git checkout -b merged-branch
```

**Step 2: Merge both branches at once**

```bash
git merge branch1 branch2
```

**Step 3: Push to remote**

```bash
git push origin merged-branch
```

### Note

The octopus merge strategy works best when there are no conflicts. If conflicts are detected, Git will abort the merge and you'll need to use Method 1 instead.

## Method 3: Using Git Rebase

This method creates a linear history by replaying commits. Use with caution, especially on shared branches.

### Step-by-Step Instructions

**Step 1: Create new branch**

```bash
git checkout main
git checkout -b merged-branch
```

**Step 2: Rebase with first branch**

```bash
git rebase branch1
```

**Step 3: Rebase with second branch**

```bash
git rebase branch2
```

**Step 4: Push (may require force push)**

```bash
# Use force push with care!
git push origin merged-branch --force-with-lease
```

### Warning

Rebasing rewrites commit history. Avoid rebasing branches that others are working on.

## Handling Merge Conflicts

Merge conflicts occur when Git can't automatically reconcile differences between branches.

### Identifying Conflicts

When a conflict occurs, Git will output:

```
CONFLICT (content): Merge conflict in <filename>
Automatic merge failed; fix conflicts and then commit the result.
```

### Resolving Conflicts

**Step 1: Check which files have conflicts**

```bash
git status
```

Look for files marked as "both modified".

**Step 2: Open conflicted files**

Conflicts are marked in the file like this:

```
<<<<<<< HEAD
Your current branch changes
=======
Incoming branch changes
>>>>>>> branch2
```

**Step 3: Resolve the conflicts**

Edit the file to keep the desired changes and remove the conflict markers:

```
# Remove the markers and keep what you want
Your desired final content here
```

**Step 4: Mark as resolved**

```bash
# After editing, stage the resolved file
git add <filename>
```

**Step 5: Complete the merge**

```bash
# If it was a merge (not rebase)
git commit

# If it was a rebase
git rebase --continue
```

### Aborting a Merge

If you want to abort and start over:

```bash
# For merge
git merge --abort

# For rebase
git rebase --abort
```

## Best Practices

1. **Always work on a clean branch**: Commit or stash changes before merging
2. **Update branches first**: Pull latest changes before creating the merged branch
3. **Test thoroughly**: After merging, test the combined code thoroughly
4. **Use descriptive branch names**: Name your merged branch clearly (e.g., `release-v2.0`, `combined-features`)
5. **Communicate with team**: Let team members know when you're creating merged branches
6. **Review changes**: Use `git diff` to review what changed during the merge
7. **Keep commit history clean**: Use meaningful commit messages
8. **Consider merge strategy**: Choose the appropriate method for your workflow

## Troubleshooting

### Problem: "Cannot create branch - already exists"

**Solution:**

```bash
# Delete the existing branch first (locally)
git branch -d merged-branch

# Or force delete if it has unmerged changes
git branch -D merged-branch

# Then create the new branch
git checkout -b merged-branch
```

### Problem: "Your local changes would be overwritten by merge"

**Solution:**

```bash
# Either commit your changes
git add .
git commit -m "Save current work"

# Or stash them temporarily
git stash
# ... perform merge ...
git stash pop
```

### Problem: Too many merge conflicts

**Solution:**

1. Merge one branch first and resolve conflicts
2. Test the code
3. Then merge the second branch
4. Consider breaking the merge into smaller steps

### Problem: Wrong files in merged branch

**Solution:**

```bash
# Reset to before the problematic merge
git reset --hard <commit-before-merge>

# Or create a new branch and start fresh
git checkout main
git checkout -b merged-branch-v2
```

### Problem: Need to merge more than two branches

**Solution:**

```bash
# Merge multiple branches sequentially
git checkout -b multi-merged-branch main
git merge branch1
git merge branch2
git merge branch3
# ... and so on
```

## Additional Resources

- [Official Git Documentation](https://git-scm.com/doc)
- [Pro Git Book](https://git-scm.com/book/en/v2)
- [Git Branching Model](https://nvie.com/posts/a-successful-git-branching-model/)

## Summary

Merging two Git branches into a new branch is a common operation that helps maintain a clean workflow. The recommended approach is:

1. Create a new branch from a stable base (usually `main`)
2. Merge the first branch
3. Merge the second branch
4. Resolve any conflicts
5. Test thoroughly
6. Push to remote

Remember to communicate with your team and follow your project's branching strategy when performing these operations.
