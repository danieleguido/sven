'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:DocumentCtrl
 * @description
 * # DocumentCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('DocumentCtrl', function ($scope, $log, $filter, $location, $routeParams, DocumentFactory, ConceptsFactory, DocumentTagsFactory) {
    $scope.document = {
      date: new Date()
    };
    $log.info($routeParams, 'loading stuff')
    $routeParams.id && DocumentFactory.query({id: $routeParams.id}, function(data){
      console.log(data);
      $scope.document = data.object;
      // once done load segments
    
    }, function(err){
      console.log(err)
    });



    $scope.save = function() {
      var doc_copy = angular.copy($scope.document),
          doc = {
            id: doc_copy.id,
            name: doc_copy.name,
            date: $filter('date')($scope.document.date, 'yyyy-MM-dd'),//$scope.document.date,
            abstract: doc_copy.abstract
          }; // translation for api purposes of some fields

      // attach new tags
      for(var tag_type in doc_copy.tags) {
        if(!doc_copy.tags[tag_type])
          continue
        doc_copy.tags[tag_type] = doc_copy.tags[tag_type].filter(function(d){
          return !d.id; // not having id
        }).map(function(d){
          return d.name
        })
      };
      

      $log.info('DocumentCtrl.save() -->', doc.name,  doc_copy.tags);

      DocumentFactory.save(doc, function(res) {
        console.debug('DocumentCtrl saved',res);
        $scope.document = res.object;
        if(res.status == 'ok') {
          toast('saved');
          $location.path('/document/' + res.object.id);
        }
      });
    };

    /*
      Available in edit text mode. Send abstract and text
    */
    $scope.saveText = function() {
      // todo: lock textareas during saving ...
      $log.info('DocumentCtrl.saveText() -->', $scope.document.name,  $scope.document.text.substring(0,45));
      DocumentFactory.saveText({
        id: $scope.document.id,
        text: $scope.document.text,
        abstract: $scope.document.abstract,
      }, function(res) {
        console.debug('DocumentCtrl.saveText() --> saved', res);
        $scope.document = res.object;
        if(res.status == 'ok') {
          toast('text has been saved');
          $location.path('/document/' + res.object.id);
        }
      });
    };

    // datepicker
    $scope.openDatePicker = function($event) {
      $event.preventDefault();
      $event.stopPropagation();
      $scope.opened = true;
    };

    // tags
    /*
      @param type should be a valid type according to sven.models.Tag, usually 'ac' or 'tm'
    */
    $scope.attachTag = function(doc, type, tag) {
      $log.info('DocumentCtrl.attachTag() -->', type, tag.name);
      DocumentTagsFactory.save({id: doc.id, tags: tag.name, type:type}, function(data){
        console.log('DocumentCtrl.attachTag() success', data);
        $scope.document.tags = data.object.tags;
      });
    }

    $scope.detachTag = function(doc, type, tag) {
      $log.info('DocumentCtrl.detachTag() -->', type, tag.name);
      DocumentTagsFactory.remove({id: doc.id, tags: tag.name, type:type}, function(data){
        console.log('DocumentCtrl.detachTag() success', data);
        $scope.document.tags = data.object.tags;
      });
    }

    /*
      SEGMENTS PART 
      ===
    */
    $scope.measure = 'tf';
    $scope.$parent.limit = 50;

    $scope.$parent.orderBy.choices = [
        {label:'tf', value:'-tf'},
        {label: 'tfidf', value:'-tf_idf'},
        {label: 'most common', value:'-distribution|-tf_idf'},
        {label:'by name a-z', value:'-segment__cluster'}
      ];
    $scope.$parent.orderBy.choice = {label: 'most common', value:'-distribution|-tf_idf'};
    
    $scope.sync = function() {
      ConceptsFactory.query(
        $scope.getParams({
          id:$scope.corpus.id,
          group_by: 'ac',
          filters: JSON.stringify({document__id:$routeParams.id})
        }), function(data){
          console.log(data); // pagination needed
          $scope.totalItems = data.meta.total_count;
          $scope.bounds     = data.meta.bounds;
          $scope.groups     = data.groups;
          $scope.clusters   = data.objects;
        });
    };

    $scope.$on(API_PARAMS_CHANGED, function(){
      $log.debug('ConceptsCtrl @API_PARAMS_CHANGED');
      $scope.sync();
    });

    $scope.sync();

    $log.debug('DocumentCtrl ready');
  });
