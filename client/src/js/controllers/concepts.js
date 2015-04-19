'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:ConceptsCtrl
 * @description
 * # ConceptsCtrl
 * Controller of the svenClientApp
 */
angular.module('sven')
  .controller('ConceptsCtrl', function ($scope, $log, $routeParams, ConceptsFactory) {
    $log.debug('ConceptsCtrl ready');
    $scope.localCorpus = {};

    $scope.measure = 'tf'; // tf | tf_idf
    $scope.group_by = {
      is_open: false,
      choices: [
        {label:'actors', value:'ac'},
        {label:'type of media', value:'tm'},
      ],
      choice: {label:'actors', value:'ac'}
    };

    /*
      group_by set
    */
    $scope.changeGroupBy = function(choice) {
      $log.info('changeGroupBy', choice);
      $scope.page = 1;
      $scope.group_by.choice = choice;
      $scope.group_by.isopen = false;
      $scope.$broadcast(API_PARAMS_CHANGED);
    };

    $scope.$parent.page = 2; // reset page
    $scope.$parent.limit = 50;

    $scope.$parent.orderBy.choices = [
        {label:'tf', value:'-tf'},
        {label: 'tfidf', value:'-tfidf'},
        //{label: 'most common', value:'-distribution|-tf_idf'},
        {label:'by name a-z', value:'segment__cluster'}
      ];
    $scope.$parent.orderBy.choice = {label:'tf', value:'-tf'};//{label: 'most common', value:'-distribution|-tf_idf'};
    
    $scope.toggleVisibility = function(concept_id) {
      // send toggle visibility then update . this below is fake...
      $log.log('toggling visibility for', concept_id);
      for( var i in $scope.clusters) {
        if($scope.clusters[i].id == concept_id)
          $scope.clusters[i].status = 'OUT';
      }
    }


    $scope.filterByTag = function(tag_slug) {
      // add a filter
      $log.log('filterByTag', tag_slug);
      
      $scope.changeFilter('tags__slug', tag_slug, {})
      
    }

    $scope.filterByConcept = function(concept_slug) {
      // add a filter
      $log.log('filterByTag', concept_slug);
      
      $scope.changeFilter('segments__cluster', concept_slug, {})
      
    }
    


    $scope.$watch('corpora', function(){// pseudo react diff. looking for the local corpus among different corpora
      for(var i=0; i<$scope.$parent.corpora.length; i++) {
        if($scope.$parent.corpora[i].id == $routeParams.id) {
          $scope.$parent.diffclone($scope.localCorpus, $scope.$parent.corpora[i])
        }
      };

    });

    /* considering filters and grouping */
    $scope.downloadConcepts = function(grouping) {
      window.open(SVEN_BASE_URL + '/api/export/corpus/' + $routeParams.id + '/concepts?' + (grouping?'group_by='+grouping:''), '_blank', '');
    };

    $scope.sync = function() {
      $routeParams.id && ConceptsFactory.query(
        $scope.getParams({
          id:$routeParams.id,
          group_by: $scope.group_by.choice.value
        }), function(data){
          console.log(data); // pagination needed
          $scope.totalItems = data.meta.total_count;
          $scope.bounds     = data.meta.bounds;
          $scope.groups     = data.groups;
          $scope.clusters   = data.objects;
          $log.info('sync() groups', $scope.groups)
          
      });
    };

    $scope.$on(API_PARAMS_CHANGED, function(){
      $log.debug('ConceptsCtrl @API_PARAMS_CHANGED');
      $scope.sync();
    });

    $scope.sync();
  });