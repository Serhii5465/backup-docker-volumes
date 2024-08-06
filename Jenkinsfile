@Library('PrepEnvForBuild') _

def agents_online = [];

def UnstashOnAgent(String label, String cmd){
    return {
        node(label){
            stage('Unstash on ' + label){
                script{
                    unstash 'src'

                    sh returnStatus: true, script: cmd
                }
            }
        }
    }
}

pipeline {
    agent {
        label 'master'
    }
    
    options { 
        skipDefaultCheckout() 
    }

    parameters {
        activeChoice choiceType: 'PT_CHECKBOX', 
        description: 'Select agents to run the build', filterLength: 1, filterable: false, 
        name: 'NODES', script: groovyScript(fallbackScript: [classpath: [], oldScript: '', sandbox: false, script: ''], 
        script: [classpath: [], oldScript: '', sandbox: false, 
        script: '''
            def GetNodesByLabel(String label){
                def nodes = []

                jenkins.model.Jenkins.get().computers.each { c ->
                if (c.node.labelString.contains("${label}")) {
                    nodes.add(c.node.selfLabel.name)
                }}

                return nodes
            }

            return GetNodesByLabel("linux_agents_vb")'''
            ])
    }

    stages {
        stage('Ping agent'){
            steps{
                script {
                    if(params.NODES.isEmpty()){
                        error("Select at least one host")
                    } else {
                        agents_online = params.NODES.split(',')
                        for (item in agents_online) {
                            CheckAgent(item)
                        }
                    }   
                }
            }
        }

        stage('Checkout git'){
            steps {
                git branch: 'main', 
                poll: false,
                credentialsId: 'backup-docker-volumes_repo_cred', 
                url: 'git@github.com:Serhii5465/backup-docker-volumes.git'

                stash includes: 'restore, **/*.py', name: 'src'
            }
        }

        stage('Deploy'){
            steps {
                script {
                    def cmd = "mkdir -p ~/scripts/docker-volume-backups; rsync --recursive --perms  --times --group --owner \
                                --specials --human-readable --stats --progress \
                                --verbose --out-format=\'%t %f %b\' . ~/scripts/docker-volume-backups"

                    def tasks = [:]

                    for (item in agents_online){
                        def label = item
                        tasks[label] = UnstashOnAgent(label, cmd)
                    }

                    parallel tasks
                }
            }
        }
    }
}