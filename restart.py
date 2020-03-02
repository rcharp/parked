import os
os.system("docker-compose stop")
os.system("docker rmi -f $(docker images -qf dangling=true)")
os.system("docker-compose up")