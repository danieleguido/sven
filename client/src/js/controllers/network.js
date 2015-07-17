'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:NetworkCtrl
 * @description
 * # NetworkCtrl
 * Controller of the svenClientApp
 */
angular.module('sven')
  .controller('NetworkCtrl', function ($scope, $log, $routeParams, graph) {
    $log.debug('NetworkCtrl ready', graph);
    $scope.graph = graph
  })