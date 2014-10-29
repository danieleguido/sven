'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:ConceptsCtrl
 * @description
 * # ConceptsCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('ConceptsCtrl', function ($scope, $log, $routeParams, ConceptsFactory) {
    $log.debug('ConceptsCtrl ready ca');
    $scope.localCorpus = {};

    $scope.measure = 'tf'; // tf | tf_idf

    $scope.$parent.page = 2; // reset page
    $scope.$parent.limit = 50;

    $scope.$parent.orderBy.choices = [
        {label:'tf', value:'tf DESC'},
        {label: 'tfidf', value:'tfidf DESC'},
        {label:'by name a-z', value:'cluster ASC'},
        {label:'by name z-a', value:'cluster DESC'}
      ];
    $scope.$parent.orderBy.choice = {label:'tf', value:'tf DESC'};
    
    $scope.toggleVisibility = function(concept_id) {
      // send toggle visibility then update . this below is fake...
      $log.log('toggling visibility for', concept_id);
      for( var i in $scope.clusters) {
        if($scope.clusters[i].id == concept_id)
          $scope.clusters[i].status = 'OUT';
      }
    }
    


    $scope.$watch('corpora', function(){// pseudo react diff. looking for the local corpus among different corpora
      for(var i=0; i<$scope.$parent.corpora.length; i++) {
        if($scope.$parent.corpora[i].id == $routeParams.id) {
          $scope.$parent.diffclone($scope.localCorpus, $scope.$parent.corpora[i])
        }
      };

    });

    $scope.downloadConcepts = function() {
      window.open('/api/export/corpus/' + $routeParams.id + '/segments', '_blank', '');
    };

    $scope.sync = function() {
      $routeParams.id && ConceptsFactory.query(
        $scope.getParams({
          id:$routeParams.id
        }), function(data){
          console.log(data); // pagination needed
          $scope.totalItems = data.meta.total_count;
          
          $scope.clusters = data.objects;
          $scope.groups = data.groups;
      });
    };

    $scope.$on(API_PARAMS_CHANGED, function(){
      $log.debug('ConceptsCtrl @API_PARAMS_CHANGED');
      $scope.sync();
    });

    $scope.sync();
  });
