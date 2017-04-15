### Classifier
* id              = Column(Integer, primary_key = True)
* name            = Column(String(250), index = True)

* owner_id = Column(Integer, ForeignKey("users.id"))

* videos = relationship(Video)
* children = relationship("Classifier")

* parent_id = Column(Integer, ForeignKey("classifiers.id"))

* training_image_list_file_path  = Column(String(550))
* training_label_list_file_path  = Column(String(550))
* training_label_name_file_path  = Column(String(550))
* epoch   = Column(Integer, default=0)

* network_type  = Column(String(250))

* model_name  = Column(String(250))

* training_status   = Column(Integer, default=0)
* training_start_time   = Column(BigInteger)
* training_end_time   = Column(BigInteger)

* evaluation_sets = relationship("EvaluationSet", secondary=classifier_evaluation_association_table, back_populates='classifiers')

* container_id   = Column(String(250))
* image_id   = Column(String(250))









