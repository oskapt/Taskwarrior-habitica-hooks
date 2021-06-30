# Taskwarrior Habitica Hook

This is a hook for [Taskwarrior](https://taskwarrior.com) that connects its task
activities to [Habitica](https://habitica.com).

It responds to the add/edit/delete actions and carries the activity to Habitica. It does not bring Habitica actions back down to Taskwarrior.

It maps Taskwarrior Priority to Habitica Difficulty:

- Low: Trivial
- None: Easy (Default)
- Medium: Medium
- High: Hard

## Architecture

To keep from polluting the local system, this application runs as an unprivileged Docker container. When the hook fires, it passes the task into the container on STDIN, along with the arguments of the command that triggered the hook. The container executes a Python script to interact with Habitica.

## Installation

1. Pull the Docker container to the system where you run Taskwarrior.

    ```bash
    docker pull monachus/task2hab:latest
    ```

2. Add the [Habitica UID and API Key](https://habitica.com/user/settings/api) to your `.taskrc`

    ```bash
    habitica.api_user=ad34dbf-526e-41ec-bfd7-58824595f9f3
    habitica.api_key=3f8a33d0-6eb1-4118-a74c-509bc3afe308
    ```

3. Install the hook file

    ```bash
    mkdir ~/.task/hooks/task2hab
    cp task2hab.sh ~/.task/hooks/task2hab
    ln -s ~/.task/hooks/task2hab/task2hab.sh ~/.task/on-add.05.task2hab
    ln -s ~/.task/hooks/task2hab/task2hab.sh ~/.task/on-modify.05.task2hab
    ```

## Usage

Use `task add`, `task edit`, and `task delete`. Only new tasks will be added to Habitica.

## Removing the Hooks

1. Delete the hooks

    ```bash
    rm ~/.task/hooks/*.task2hab
    rm -fr ~/.task/hooks/task2hab
    ```

2. Delete the container

    ```bash
    docker rmi monachus/task2hab:latest
    ```

## Credits

- The original Python 2 script came from [fplourde](https://github.com/fplourde/Taskwarrior-habitica-hooks).
- Modifications for Python 3 came from [Shadow53](https://github.com/fplourde/Taskwarrior-habitica-hooks/pull/12).
