# docsite

Generate a HTML static website from a collection of MS Word documents in folders

You can build this using the command:

```shell
docker build -t docsite .
```

And you can run it using the command:

```shell
docker run -v $(pwd):/data --rm -it -e ZIP_LOCATION=/data/x.zip -e ROOT_PATH=datalab.landesmuseum  docsite:latest
```
