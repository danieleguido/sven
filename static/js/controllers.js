'use strict';

var CONTROLLER_STATUS_AVAILABLE = 'available',
    CONTROLLER_STATUS_WORKING = 'busy';

/* Controllers */

angular.module('sven.controllers', [])
  /*

    Handle the main view. Unused
    ===
  
  */
  .controller('indexCtrl', ['$scope', function($scope) {
    
  }])
  /*

    Handle the profile view.
    ===
  
  */
  .controller('profileCtrl', ['$scope', 'ProfileFactory', function($scope, ProfileFactory) {
    $scope.profile = {};

    ProfileFactory.query(function(data){
      console.log(data)
      $scope.profile = data.object;
    });
  }])
  /*

    Handle the corpus list view.
    ===
  
  */
  .controller('corpusListCtrl', ['$scope', 'CorpusListFactory', function($scope, CorpusListFactory) {
    $scope.items = [];
    $scope.status = CONTROLLER_STATUS_WORKING;

    CorpusListFactory.query(function(data){
      console.log(data)
      $scope.howmany = data.meta.total_count;
      $scope.items = data.objects;
      $scope.status = CONTROLLER_STATUS_AVAILABLE;
    });

    $scope.addTodo = function(){
      if($scope.status != CONTROLLER_STATUS_AVAILABLE)
        return;
      $scope.status = CONTROLLER_STATUS_WORKING;

      CorpusListFactory.save({}, {
        name: $scope.name,
      }, function(data){
        $scope.status = CONTROLLER_STATUS_AVAILABLE;
        $scope.items = data.objects;
      });
    }
  }])
  .controller('corpusCtrl', ['$scope','$routeParams','CorpusFactory', 'DocumentListFactory', function($scope, $routeParams, CorpusFactory, DocumentListFactory) {
    CorpusFactory.query({id: $routeParams.id}, function(data){
      $scope.corpus = data.object;
      
    });
    DocumentListFactory.query({id: $routeParams.id}, function(data){
      $scope.howmany = data.meta.total_count;
      $scope.documents = data.objects;
    });
  }])
  .controller('MyCtrl2', [function() {

  }]);