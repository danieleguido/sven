'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:MainCtrl
 * @description
 * # MainCtrl
 * Controller of the svenClientApp
 */
angular.module('svenClientApp')
  .controller('MainCtrl', function ($scope, $log, $location) {
    $log.debug('MainCtrl ready');

    $scope.$watch('corpus', function() {
      if($scope.corpus.id)
        $location.path('corpus/' + $scope.corpus.id + '/documents');
    })

  });
