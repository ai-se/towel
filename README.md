Why towel?
-----
According to The Hitchhiker's Guide to the Galaxy, *"A towel is about the most massively useful thing an interstellar hitchhiker can have. Partly it has great practical value. You can wrap it around you for warmth as you bound across the cold moons of Jaglan Beta; you can lie on it on the brilliant marble-sanded beaches of Santraginus V, inhaling the heady sea vapors; you can sleep under it beneath the stars which shine so redly on the desert world of Kakrafoon; use it to sail a miniraft down the slow heavy River Moth; wet it for use in hand-to-hand-combat; wrap it round your head to ward off noxious fumes or avoid the gaze of the Ravenous Bugblatter Beast of Traal (such a mind-boggingly stupid animal, it assumes that if you can't see it, it can't see you); you can wave your towel in emergencies as a distress signal, and of course dry yourself off with it if it still seems to be clean enough."*

Setting up Towel
-----


1. Installing Elasticsearch:
  + Download and extract Elasticsearch 2.3.4 (or newer) from [here](https://www.elastic.co/downloads/elasticsearch).
  + You'll also need to install [JAVA](http://java.com/en/download/manual.jsp)
    - If you haven't already, configure JAVA_HOME. (see [instructions](https://confluence.atlassian.com/doc/setting-the-java_home-variable-in-windows-8895.html))
  + To run ES, we run `elasticsearch.bat` located in the bin folder (in elasticsearch the directory) from a command window. This will start ElasticSearch running in the foreground in the console, meaning we'll see errors in the console and can shut it down using `CTRL+C`. *Note: We don't have to start this manually. Our code will automatically spawn an ES process if its not running already.*
  + Append `X:\<elasticsearch-directory>\bin\` folder to windows PATH (update PATH variable in *Control Panel > System > Advanced System Settings > Environment Variables*)
  + To get started with Elastisearch, a lots of cool resources are available in (elastic.co)[elastic.co] and a good introduction [here](http://joelabrahamsson.com/elasticsearch-101/).
  
2. Setting up Python:
  + We use anaconda by continuum.io (see [Why?](https://www.continuum.io/why-anaconda))
    - We won't need the entire distribution. [Download](http://conda.pydata.org/miniconda.html) & install a minimal version of anaconda.
  + Make sure you select add to PATH during install.
  + Next, navigate to towel, and run `setup.bat`. This will install all the dependencies needed to run the sandbox.

3. Running script:
  + Navigate to *src > site* and run `index.py`.
  + There are some optional flags. 
    ![image](https://cloud.githubusercontent.com/assets/1433964/16997361/14b4f41a-4e83-11e6-995c-09a8b5d1ff77.png)

  + If all is well, you'll be greeted by this:
      ![image](https://cloud.githubusercontent.com/assets/1433964/16996958/7aa4d72e-4e81-11e6-838f-da8b24e78c3c.png)

4. The Interface:
  + Fire up your browser and go to `http://localhost:8000/hello/`. You'll see a page like below:
    ![image](https://cloud.githubusercontent.com/assets/1433964/16997126/1c3a89e4-4e82-11e6-8aa7-ee596ace709b.png)
