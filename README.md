If you want to run Wordpress in Docker, there are two options.
The "official" way, is to take the Wordpress out of the Wordpress-Dockerimage and put it onto a shared storage. 
So that you're basically left with a Dockerimage, that contains and runs a preconfigured webserver.
That kinda defeats the purpose of having a Dockerimage.

The other option, is to put all required things (including plugins and themes) in the Dockerimage.
That is the preferred option, but requires some effort and makes it more difficult to update Wordpress or the plugins.
But that is, where this tool comes into play. 

# What is it?
It fetches the repository containing your customized Wordpress (config, plugins, themes, Dockerfile ...), 
checks if there are newer versions, update the versions if required, commits everything, wait for the build-pipeline to finish
and then trigger the release-pipeline to rollout the new image.

# Requirements
The mechanism that interacts with the pipelines, only supports Azure Devops.
The repository is also required to follow some conventions.

For more details about the whole setup, read the following blog-series: 
https://blog.hmg.dev/2021/01/25/wordpress-in-kubernetes-teil-1-anforderungen-und-problem-aeh-herausforderungen/
