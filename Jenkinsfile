@Library(['PrepEnvForBuild', 'DeployWinAgents']) _

node('master') {
    def config = [
        platform: "linux",
        git_repo_url : "git@github.com:Serhii5465/backup-docker-volumes.git",
        git_branch : "main",
        git_cred_id : "backup-docker-volumes_repo_cred",
        stash_includes : "*",
        stash_excludes : "",
        command_deploy : "",
        func_deploy : ""
    ]

    DeployArtifactsPipelineWinAgents(config)
}