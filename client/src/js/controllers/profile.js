'use strict';

/**
 * @ngdoc function
 * @name sven.controller:ProfileCtrl
 * @description
 * # ProfileCtrl
 * Controller of the sven
 */
angular.module('sven')
  .controller('ProfileCtrl', function ($scope, $log, ProfileFactory) {
    $log.debug('ProfileCtrl ready');
    $scope.save = function() {
      ProfileFactory.save(angular.copy($scope.$parent.profile), function(data) {
        console.log('back to me',data);
        $scope.$parent.profile = data.object;
      });
    };
  });
