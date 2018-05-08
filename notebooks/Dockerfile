FROM radanalyticsio/jupyter-notebook-py3.5

USER root
RUN mkdir /data

ENV NB_USER=nbuser
ENV NB_UID=1011

EXPOSE 8888

USER $NB_UID

USER root

RUN chown -R $NB_USER:root /home/$NB_USER /data \
    && find /home/$NB_USER -type d -exec chmod g+rwx,o+rx {} \; \
    && find /home/$NB_USER -type f -exec chmod g+rw {} \; \
    && find /data -type d -exec chmod g+rwx,o+rx {} \; \
    && find /data -type f -exec chmod g+rw {} \; \
    && /opt/conda/bin/conda install --quiet --yes -c conda-forge spacy \
    && /opt/conda/bin/conda install --quiet --yes terminado \
    && /opt/conda/bin/pip install vaderSentiment \
    && /opt/conda/bin/python -m spacy download en \
    && ( /opt/conda/bin/conda clean -qtipsy || echo "conda clean FAILED" ) \
    && chmod -f g+rw /notebooks $(find /notebooks) 

ADD *.txt *.txt.gz /notebooks/
ADD *.ipynb /notebooks/

RUN chmod -f g+rw /notebooks $(find /notebooks) 

USER $NB_UID
ENV HOME /home/$NB_USER

LABEL io.k8s.description="PySpark Jupyter Notebook." \
      io.k8s.display-name="PySpark Jupyter Notebook." \
      io.openshift.expose-services="8888:http"

CMD ["/entrypoint", "/usr/local/bin/start.sh"]