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

    $scope.$watch('corpora', function(){// pseudo react diff. looking for the local corpus among different corpora
      for(var i=0; i<$scope.$parent.corpora.length; i++) {
        if($scope.$parent.corpora[i].id == $routeParams.id) {
          $scope.$parent.diffclone($scope.localCorpus, $scope.$parent.corpora[i])
        }
      };

    });

    $routeParams.id && ConceptsFactory.query({id: $routeParams.id}, function(data){
      console.log(data); // pagination needed
      $scope.clusters = data.objects;
    });
  });
