'use strict';

/* Controllers */

angular.module('sven.controllers', []).
  controller('corpusListCtrl', ['$scope', 'CorpusListFactory', function($scope, CorpusListFactory) {
    CorpusListFactory.query(function(data){
      $scope.howmany = data.meta.total_count;
      $scope.corpora = data.objects;
      
    });
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