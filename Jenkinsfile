@Library(['PrepEnvForBuild', 'DeployWinAgents']) _

node('master') {
    def config = [
        platform: "linux",
        git_repo_url : "git@github.com:Serhii5465/backup-docker-volumes.git",
        git_branch : "main",
        git_cred_id : "backup-docker-volumes_repo_cred",
        stash_includes : "**/*.py, requirements.txt",
        stash_excludes : "",
        command_deploy : "mkdir -p /data/scripts/docker-volume-backups; chmod 700 /data/scripts/docker-volume-backups; \
                                rsync --recursive --perms  --times --group --owner \
                                --specials --human-readable --stats --progress \
                                --verbose --out-format=\'%t %f %b\' . /data/scripts/docker-volume-backups; \
                                chmod 700 -R /data/scripts/docker-volume-backups",
        func_deploy : ""
    ]

    DeployArtifactsPipelineOnAgents(config)
}